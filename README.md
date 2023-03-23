# Practica-2

Se incluyen los siguientes archivos:
 - Practica 2 Jose Ignacio Alba Rodriguez en papel.pdf correspondiente al ejercicio en papel con las demostraciones 
 - Practica 2 Jose Ignacio Alba Rodriguez.py correspondiente al codigo principal en python
 - anadiendo_limites_al_puente.py

Este ultimo archivo es una ligera modificación del codigo principal. En esta variacion, se añade una restriccion sobre la capacidad simultanea de agentes en el puente. Los cambios que tiene respecto al codigo original es que se añade una restriccion a la hora de hacer el wait_for para las variables de condicion que permiten el acceso al puente, y esto obliga a añadir unos notify cuando alguien sale del puente. Consideré interesante añadir el cambio debido a que resulta mas natural que la capacidad del puente sea limitada y no puedan cruzar una cantidad demasiado grande de coches en fila, ya que la motivacion de la practica surgia de que el tamaño del puente era bastante reducido.
