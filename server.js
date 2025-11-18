import 'dotenv/config';
import express from 'express';
import http from 'http';
import { WebSocketServer } from 'ws';
import { SpeechClient } from '@google-cloud/speech';

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/stream' });

// UI
app.use(express.static('public'));

const speechClient = new SpeechClient();

/** Utilidad: crea un stream de Google STT con config dada */
function createStream(ws, cfg) {
  const recognizeStream = speechClient
    .streamingRecognize(cfg)
    .on('error', (err) => {
      console.error('Google STT error:', err?.message || err);
      if (ws.readyState === 1) {
        ws.send(JSON.stringify({ type: 'error', message: String(err?.message || err) }));
      }
    });
  return recognizeStream;
}

/** Config base para el stream principal (transcripción) */
function mainConfig({ languageCode = 'es-PE', sampleRateHertz = 16000 } = {}) {
  return {
    config: {
      encoding: 'LINEAR16',
      sampleRateHertz,
      languageCode,
      enableAutomaticPunctuation: true,
      model: 'default',
      // Puedes añadir vocabulario médico aquí si quieres:
      // speechContexts: [{ phrases: ["cefalea","saturación","auscultación"], boost: 15.0 }]
    },
    interimResults: true
  };
}

/** Config para el stream de comandos (fuerte sesgo a “continuar”) */
function commandConfig({ languageCode = 'es-PE', sampleRateHertz = 16000 } = {}) {
  return {
    config: {
      encoding: 'LINEAR16',
      sampleRateHertz,
      languageCode,
      enableAutomaticPunctuation: false,
      model: 'default',
      speechContexts: [{
        phrases: [
          // “continuar” y formas frecuentes
          "continuar","continua","continúa","continuo","continuamos","continuemos","continúe","continúen"
        ],
        boost: 20.0
      }]
    },
    interimResults: true
  };
}

/** Regex robusto para “continuar” y variaciones */
const RE_CONTINUAR_ANY = /\b(continuar|continua|continúa|continuo|continuamos|continuemos|continúe|continúen)\b/i;

wss.on('connection', (ws) => {
  console.log('WS: cliente conectado');

  // Estado
  let mode = 'active'; // 'active' | 'paused'
  let lastOpts = { languageCode: 'es-PE', sampleRateHertz: 16000 };

  // Streams
  let mainStream = null; // transcribe texto normal
  let cmdStream  = null; // detecta “continuar” cuando está pausado

  // Helpers stream
  const startMain = (opts = {}) => {
    lastOpts = { ...lastOpts, ...opts };
    stopMain();
    const cfg = mainConfig(lastOpts);
    mainStream = createStream(ws, cfg)
      .on('data', (data) => {
        // En modo active: mandamos transcripción al cliente
        if (mode !== 'active') return;
        const result = data.results?.[0];
        if (!result) return;
        const alt = result.alternatives?.[0];
        if (ws.readyState === 1) {
          ws.send(JSON.stringify({
            type: 'transcript',
            transcript: alt?.transcript ?? '',
            isFinal: !!result.isFinal
          }));
        }
      });
  };

  const stopMain = () => {
    if (mainStream) {
      try { mainStream.end(); } catch {}
      try { mainStream.destroy(); } catch {}
    }
    mainStream = null;
  };

  const startCmd = () => {
    stopCmd();
    const cfg = commandConfig(lastOpts);
    cmdStream = createStream(ws, cfg)
      .on('data', (data) => {
        if (mode !== 'paused') return;
        const result = data.results?.[0];
        if (!result) return;
        const alt = result.alternatives?.[0];
        const t = (alt?.transcript || '').toLowerCase();
        // Si aparece cualquier forma de “continuar”, reanuda
        if (RE_CONTINUAR_ANY.test(t)) {
          resumeFromServer();
        }
      });
  };

  const stopCmd = () => {
    if (cmdStream) {
      try { cmdStream.end(); } catch {}
      try { cmdStream.destroy(); } catch {}
    }
    cmdStream = null;
  };

  const pauseFromClient = () => {
    if (mode === 'paused') return;
    mode = 'paused';
    // Apagamos stream principal y encendemos stream de comandos
    stopMain();
    startCmd();
    if (ws.readyState === 1) {
      ws.send(JSON.stringify({ type: 'status', message: 'paused_by_command' }));
    }
  };

  const resumeFromServer = () => {
    if (mode === 'active') return;
    mode = 'active';
    // Apagamos comando y encendemos principal (reiniciado)
    stopCmd();
    startMain();
    if (ws.readyState === 1) {
      ws.send(JSON.stringify({ type: 'status', message: 'resumed_by_command' }));
    }
  };

  // Enrutamiento de audio: va al stream según el modo
  ws.on('message', (data, isBinary) => {
    if (isBinary) {
      // PCM16 desde el navegador
      const buf = Buffer.isBuffer(data) ? data : Buffer.from(data);
      // En active -> al mainStream; en paused -> al cmdStream
      if (mode === 'active') {
        if (mainStream) { try { mainStream.write(buf); } catch {} }
      } else {
        if (cmdStream)  { try { cmdStream.write(buf); }  catch {} }
      }
      return;
    }

    let msg;
    try { msg = JSON.parse(data.toString()); } catch { return; }

    switch (msg.type) {
      case 'start':
        mode = 'active';
        stopCmd();
        startMain({ languageCode: msg.languageCode, sampleRateHertz: msg.sampleRateHertz });
        if (ws.readyState === 1) ws.send(JSON.stringify({ type: 'status', message: 'streaming_started' }));
        break;

      case 'stop':
        stopMain();
        stopCmd();
        if (ws.readyState === 1) ws.send(JSON.stringify({ type: 'status', message: 'streaming_stopped' }));
        break;

      case 'pause_by_command':
        pauseFromClient();
        break;

      case 'resume_by_command':
        // Fuerza reanudar (por si el cliente manda reanudar manualmente)
        resumeFromServer();
        break;
    }
  });

  ws.on('close', () => {
    stopMain();
    stopCmd();
    console.log('WS: cliente desconectado');
  });
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => console.log(`Servidor listo en http://localhost:${PORT}`));