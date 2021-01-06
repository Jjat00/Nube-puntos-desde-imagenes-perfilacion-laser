import numpy as np 
import vedo
import cv2

def loadImages(nImages):
    """ 
    loadImages: Carga el conjunto imágenes
    paramters: numero de imágenes
    return: imágenes
    """
    images = []
    for nImage in range(1, nImages):
        image = cv2.imread('imagesReconstruccion/Line (%i).bmp' % (nImage), 0)
        images.append(image)
    return images
    
def knNeighbors(vertices, nNeighbors):
    """ 
    knNeighbors: disminuye el ruido y agrupo los puntos con sus vecionos más cercanos
    parameters: vertices y el número de vecinos a tener en cuenta
    return: nueva nube de puntos
    """
    vertices = vedo.Points(vertices)
    newPointCloud = []
    for i in range(vertices.N()):
        pt = vertices.points()[i]
        ids = vertices.closestPoint(pt, N = nNeighbors, returnIds=True)
        newPointCloud.append(
            np.mean(vertices.points()[ids], axis=0).tolist())
    newPointCloud = np.array(newPointCloud)
    return newPointCloud

def esqueletizar(image):
    """ 
    esqueletizar: reduce el grosor de la linea original
    parameters: imágen de perfilación láser
    return: nueva imagen 
    """
    # suavizamos un poco la imágen con un filtro gaussiano y kernel de (3,3)
    GBlur = cv2.GaussianBlur(image, (3, 3), 0)
    # generamos matriz de ceros para guardar la imagen resultante
    skel = np.zeros(GBlur.shape, np.uint8)
    size = np.size(image)
    # binarizamos la imágen con límites de 15 y 255
    ret, img = cv2.threshold(GBlur, 15, 255, 0)
    # empezamos el proceso de esqueletización
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    done = False
    while(not done):
        eroded = cv2.erode(img, element)
        temp = cv2.dilate(eroded, element)
        temp = cv2.subtract(img, temp)
        skel = cv2.bitwise_or(skel, temp)
        img = eroded.copy()
        zeros = size - cv2.countNonZero(img)
        if zeros == size:
            done = True
    return skel

def toXYZ(skel, delta):
    """
    toXYZ: transforma la imágen a una nube de puntos 3D
    parameters: imagen esqueletizada y el delta que hay entre cada imágen
    return: coordenadas (x,y,z) de la nube de puntos 
    """
    # identificamos las coordenadas en las que está la linea del láser
    coordenadas = np.where(skel >= 100)
    # obtenemos coordenadas (x,y)
    x = np.array(coordenadas[0])
    y = np.array(coordenadas[1])
    # creamos tercer coordenada z
    z = 0*x + delta
    # creamos coordenadas (x, y, z)
    xyz = np.vstack((x, y, z))
    xyz = xyz.transpose()
    # recortamos la nube de puntos
    xyz = xyz[y > 520]
    newY = y[y > 520]
    newYyz = xyz[newY < 720]
    return newYyz

def reconstruction(images, xyz, count):
    """
    reconstruction: une cada una de las nubes de puntos generada por cada una de las imágenes
    parameters: imagenes, vertices, contador
    return: nube de puntos de todas las imágenes
    """
    delta = 5
    newXyz = xyz
    print('imagen No: ', count)
    if count < len(images)-1:
        skel = esqueletizar(images[count])
        xyz1 = toXYZ(skel, delta*count)
        xyz = np.concatenate((newXyz, xyz1))
        count = count + 1
        newXyz = reconstruction(images, xyz, count)
    return newXyz

def start():
    """ 
    start: empieza el procedimiento de reconstrucción
    """
    print('init...')
    # Cargamos las imágenes
    images = loadImages(59)

    # hace una primera tranformación para inicializar la recontrucción
    skel = esqueletizar(images[0])
    xyz = toXYZ(skel, 0)
    # empieza la reconstrucción
    xyz = reconstruction(images[5:-3], xyz, 1)
    # si se desea se aplica el filtro 
    #xyz = knNeighbors(xyz, 5)
    
    # visualiza la nube de puntos resultante
    vertex = vedo.Points(xyz, r=2.0)
    scalars = vertex.points()[:, 0]
    # agrega el falso color jet
    vertex.pointColors(-scalars, cmap="jet")
    vedo.show(vertex, bg='k', axes=9)

if __name__ == "__main__":
    start()
