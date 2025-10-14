import random
import math
from typing import Tuple
from geopy import distance
from geopy.point import Point
import random
import math
def generate_random_points_around(lat: float, lon: float, radius_meters: int = 5, count: int = 1) -> list[Tuple[float, float]]:
    """
    Generate random points within radius_meters of the given lat/lon.
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point  
        radius_meters: Radius in meters (default 5)
        count: Number of points to generate
    
    Returns:
        List of (latitude, longitude) tuples
    """
    points = []
    
    # Conversiones aproximadas para metros a grados
    # 1 grado de latitud ≈ 111,320 metros
    # 1 grado de longitud ≈ 111,320 * cos(latitud) metros
    lat_conversion = 111320.0
    lon_conversion = 111320.0 * math.cos(math.radians(lat))
    
    for _ in range(count):
        # Generar ángulo aleatorio (0 a 2π)
        angle = random.uniform(0, 2 * math.pi)
        
        # Generar distancia aleatoria (0 a radius_meters)
        # Usar sqrt para distribución uniforme en área circular
        distance = math.sqrt(random.uniform(0, 1)) * radius_meters
        
        # Convertir a desplazamientos en grados
        delta_lat = (distance * math.cos(angle)) / lat_conversion
        delta_lon = (distance * math.sin(angle)) / lon_conversion
        
        # Calcular nuevas coordenadas
        new_lat = lat + delta_lat
        new_lon = lon + delta_lon
        
        points.append((new_lat, new_lon))
    
    return points



def generate_random_points_geopy(lat: float, lon: float, radius_meters: int = 5, count: int = 1) -> list[Tuple[float, float]]:
    """Generate random points using geopy for more accurate calculations."""
    points = []
    center = Point(lat, lon)
    
    for _ in range(count):
        # Ángulo aleatorio
        bearing = random.uniform(0, 360)
        
        # Distancia aleatoria con distribución uniforme en área
        dist_meters = math.sqrt(random.uniform(0, 1)) * radius_meters
        
        # Calcular nuevo punto
        new_point = distance.distance(meters=dist_meters).destination(center, bearing)
        points.append((new_point.latitude, new_point.longitude))
    
    return points