// Los tokens (design/tokens.json) y Chaski (avatar/) viven fuera de movil/ y se importan de ahí,
// sin copias: si cambian en el repo, la app los toma en el siguiente build.
const path = require('path');
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
// Los archivos de ../avatar buscan sus dependencias (asset-registry) en el node_modules de la app.
config.resolver.nodeModulesPaths = [path.resolve(__dirname, 'node_modules')];
config.watchFolders = [
  path.resolve(__dirname, '../design'),
  path.resolve(__dirname, '../avatar'),
  // url.json: la dirección del túnel que publica Ricardo con servicio/publicar_url.sh.
  path.resolve(__dirname, '../ricardo-artifacts/servicio'),
  // banco.json: el banco real de frases verificadas (D34), empaquetado como respaldo de GET /banco.
  path.resolve(__dirname, '../app/chaski'),
];
module.exports = config;
