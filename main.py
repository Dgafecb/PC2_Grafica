import tempfile
import os
from flask import Flask, request, redirect, send_file
from skimage import io
import base64
import glob
import numpy as np

app = Flask(__name__)

main_html = """
<html>
<head></head>
<script>
  var mousePressed = false;
  var lastX, lastY;
  var ctx;

  function getRndInteger(min, max) {
    return Math.floor(Math.random() * (max - min) ) + min;
  }

  function InitThis() {
      ctx = document.getElementById('myCanvas').getContext("2d");

      // Lista de símbolos romanos básicos
      var simbolos_romanos = ["I", "V", "X", "L", "C", "D", "M"];
      var random = Math.floor(Math.random() * simbolos_romanos.length);
      var aleatorio = simbolos_romanos[random];

      document.getElementById('mensaje').innerHTML  = 'Dibujando el símbolo romano ' + aleatorio;
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
      // Use the identity matrix while clearing the canvas
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  }

  //https://www.askingbox.com/tutorial/send-html5-canvas-as-image-to-server
  function prepareImg() {
     var canvas = document.getElementById('myCanvas');
     document.getElementById('myImage').value = canvas.toDataURL();
  }

</script>
<body onload="InitThis();">
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
      <form method="post" action="upload" onsubmit="javascript:prepareImg();"  enctype="multipart/form-data">
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
    return(main_html)


@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Obtener la imagen y el símbolo romano
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        aleatorio = request.form.get('numero')
        print(aleatorio)
        
        # Define the base directory inside the container (adjust this path as necessary)
        base_dir = '/app/uploads/'  # Ensure this folder exists in your Docker container
        
        # Create the directory if it doesn't exist
        target_dir = os.path.join(base_dir, aleatorio)
        os.makedirs(target_dir, exist_ok=True)
        
        # Save the image in the appropriate folder
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir=target_dir) as fh:
            fh.write(base64.b64decode(img_data))
        
        print("Image uploaded successfully")
    except Exception as err:
        print("Error occurred")
        print(err)

    return redirect("/", code=302)



import os
import glob
import numpy as np
from skimage import io

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    simbolos_romanos = ["I", "V", "X", "L", "C", "D", "M"]
    digits = []

    # Cuando utilizemos docker lo guardaremos en el siguiente directorio
    base_dir = '/app/uploads/'
    
    for simbolo in simbolos_romanos:
        # Buscaremos las imagenes dentro de uploads
        filelist = glob.glob(os.path.join(base_dir, simbolo, '*.png'))
        
        # Para que ignore las imagenes si el folder esta vacio
        if not filelist:
            continue
        
        # Leer las imágenes y obtener el canal alfa (si es necesario)
        images_read = io.concatenate_images(io.imread_collection(filelist))
        images_read = images_read[:, :, :, 3]  # Si las imágenes tienen canal alfa, obtenerlo
        
        # Crear un array con el símbolo romano correspondiente para cada imagen
        digits_read = np.array([simbolo] * images_read.shape[0])
        
        images.append(images_read)
        digits.append(digits_read)
    
    # Concatenar todas las imágenes y los dígitos correspondientes
    images = np.vstack(images)
    digits = np.concatenate(digits)
    
    # Guardar los datos en archivos .npy
    np.save(os.path.join(base_dir, 'X.npy'), images)
    np.save(os.path.join(base_dir, 'y.npy'), digits)
    
    return "Dataset preparado correctamente!"


@app.route('/X.npy', methods=['GET'])
def download_X():
    file_path = os.path.join('/app/uploads', 'X.npy') # Agregamos la ruta completa uploads/X.npy
    return send_file(file_path)
@app.route('/y.npy', methods=['GET'])
def download_y():
    file_path = os.path.join('/app/uploads', 'y.npy')
    return send_file(file_path)

if __name__ == "__main__":
    simbolos_romanos = ["I", "V", "X", "L", "C", "D", "M"]
    for simbolo in simbolos_romanos:
        if not os.path.exists(str(simbolo)):
            os.mkdir(str(simbolo))
    app.run()
