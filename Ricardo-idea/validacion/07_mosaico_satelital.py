"""Baja un mosaico satelital de Lima y lo deja como una sola imagen.

La CSP de los artifacts bloquea tiles externos, asi que la imagen viaja con la
pagina. Fuente: Esri World Imagery. Atribucion obligatoria en el pie del mapa.
"""
import io, math, pathlib, time, urllib.request

from PIL import Image

Z = 13
W, S, E, N = -77.20, -12.35, -76.70, -11.70
URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
UA = {"User-Agent": "Mozilla/5.0 (research; crime corridors Lima)"}


def tile_x(lon, z):
    return int((lon + 180.0) / 360.0 * 2 ** z)


def tile_y(lat, z):
    phi = math.radians(lat)
    return int((1 - math.log(math.tan(phi) + 1 / math.cos(phi)) / math.pi) / 2 * 2 ** z)


x0, x1 = tile_x(W, Z), tile_x(E, Z)
y0, y1 = tile_y(N, Z), tile_y(S, Z)
ancho, alto = (x1 - x0 + 1), (y1 - y0 + 1)
print(f"z={Z}  tiles {ancho}x{alto} = {ancho*alto}  -> {ancho*256}x{alto*256} px", flush=True)

mosaico = Image.new("RGB", (ancho * 256, alto * 256))
fallidos = 0
for i, x in enumerate(range(x0, x1 + 1)):
    for j, y in enumerate(range(y0, y1 + 1)):
        try:
            datos = urllib.request.urlopen(
                urllib.request.Request(URL.format(z=Z, x=x, y=y), headers=UA), timeout=30).read()
            mosaico.paste(Image.open(io.BytesIO(datos)), (i * 256, j * 256))
        except Exception as e:
            fallidos += 1
            print("falla", x, y, str(e)[:40], flush=True)
        time.sleep(0.02)
    print(f"columna {i+1}/{ancho}", flush=True)

destino = pathlib.Path("viz/datos")
destino.mkdir(parents=True, exist_ok=True)
escala = 2400 / mosaico.width
final = mosaico.resize((2400, int(mosaico.height * escala)), Image.LANCZOS)
final.save(destino / "satelite.jpg", "JPEG", quality=72, optimize=True)

# los limites exactos del mosaico, en coordenadas de mundo de Web Mercator a z=Z
meta = {"z": Z, "x0": x0, "y0": y0, "ancho_tiles": ancho, "alto_tiles": alto,
        "px_ancho": final.width, "px_alto": final.height}
(destino / "satelite.js").write_text("window.SATELITE=" + str(meta).replace("'", '"') + ";")
print("tiles fallidos:", fallidos)
print("archivo:", (destino / "satelite.jpg").stat().st_size // 1024, "KB", final.size)
