import tempfile
import os
from flask import Flask, request, redirect, send_file, render_template_string
from skimage import io
import base64
import glob
import numpy as np

app = Flask(__name__)

# HTML con plantilla dinámica para filtrar símbolos romanos
main_html_template = """
<html>
<head></head>
<script>
  var mousePressed = false;
  var lastX, lastY;
  var ctx;

  function InitThis(symbols) {
      ctx = document.getElementById('myCanvas').getContext("2d");

      // Filtra la lista de símbolos romanos basados en la URL
      var clases = symbols.split(',');
      var random = Math.floor(Math.random() * clases.length);
      var aleatorio = clases[random];

      document.getElementById('mensaje').innerHTML  = 'Dibuja:  ' + aleatorio;
      document.getElementById('numero').value = aleatorio;

      $('#myCanvas').mousedown(function (e) {
          mousePressed = true;
          Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
      });

      $('#myCanvas').mousemove(function (e) {
          if (mousePressed) {
              Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
          }
      });

      $('#myCanvas').mouseup(function (e) {
          mousePressed = false;
      });
  	    $('#myCanvas').mouseleave(function (e) {
          mousePressed = false;
      });
  }

  function Draw(x, y, isDown) {
      if (isDown) {
          ctx.beginPath();
          ctx.strokeStyle = 'black';
          ctx.lineWidth = 11;
          ctx.lineJoin = "round";
          ctx.moveTo(lastX, lastY);
          ctx.lineTo(x, y);
          ctx.closePath();
          ctx.stroke();
      }
      lastX = x; lastY = y;
  }

  function clearArea() {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  }

  function prepareImg() {
     var canvas = document.getElementById('myCanvas');
     document.getElementById('myImage').value = canvas.toDataURL();
  }
</script>
<body onload="InitThis('{{ symbols }}');">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js" type="text/javascript"></script>
    <script type="text/javascript" ></script>
    <div align="left">
      <img src="https://upload.wikimedia.org/wikipedia/commons/f/f7/Uni-logo_transparente_granate.png" width="300"/>
    </div>
    <div align="center">
        <h1 id="mensaje">Dibujando...</h1>
        <canvas id="myCanvas" width="200" height="200" style="border:2px solid black"></canvas>
        <br/>
        <br/>
        <button onclick="javascript:clearArea();return false;">Borrar</button>
    </div>
    <div align="center">
      <form method="post" action="/{{ name }}/upload" onsubmit="javascript:prepareImg();"  enctype="multipart/form-data">
      <input id="numero" name="numero" type="hidden" value="">
      <input id="myImage" name="myImage" type="hidden" value="">
      <input id="bt_upload" type="submit" value="Enviar">
      </form>
    </div>
</body>
</html>
"""

@app.route("/")
def main():
    return redirect("/joshua")

@app.route("/<name>")
def draw_page(name):
    # Filtrar los símbolos basados en la URL
    if name.lower() == "joshua":
        symbols = "Joshua-gato,Joshua-mesa"
    elif name.lower() == "gabriel":
        symbols = "Gabriel-gato,Gabriel-mesa"
    else:
        return "Página no encontrada", 404
    
    # Renderizar la plantilla HTML con los símbolos correspondientes
    return render_template_string(main_html_template, symbols=symbols, name=name)


@app.route('/<name>/upload', methods=['POST'])
def upload(name):
    try:
        # Obtener la imagen y el símbolo
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        aleatorio = request.form.get('numero')
        print(aleatorio)
        
        base_dir = './uploads/'
        target_dir = os.path.join(base_dir, aleatorio)
        os.makedirs(target_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir=target_dir) as fh:
            fh.write(base64.b64decode(img_data))

        print("Imagen cargada correctamente")
    except Exception as err:
        print("Error al cargar la imagen")
        print(err)

    # Redireccionar de vuelta a la misma ruta
    return redirect(f"/{name}", code=302)

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    clases = ["Gabriel-gato", "Joshua-gato", "Gabriel-mesa", "Joshua-mesa"]
    digits = []

    base_dir = './uploads/'
    for simbolo in clases:
        filelist = glob.glob(os.path.join(base_dir, simbolo, '*.png'))

        if not filelist:
            continue

        images_read = io.concatenate_images(io.imread_collection(filelist))
        images_read = images_read[:, :, :, 3]

        digits_read = np.array([simbolo] * images_read.shape[0])

        images.append(images_read)
        digits.append(digits_read)

    images = np.vstack(images)
    digits = np.concatenate(digits)

    np.save(os.path.join(base_dir, 'X.npy'), images)
    np.save(os.path.join(base_dir, 'y.npy'), digits)

    return "¡Dataset preparado correctamente!"

@app.route('/X.npy', methods=['GET'])
def download_X():
    file_path = os.path.join('./uploads', 'X.npy')
    return send_file(file_path)

@app.route('/y.npy', methods=['GET'])
def download_y():
    file_path = os.path.join('./uploads', 'y.npy')
    return send_file(file_path)

if __name__ == "__main__":
    app.run()
