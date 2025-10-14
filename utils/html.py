from bs4 import BeautifulSoup
from typing import Optional, Dict


def get_user_info(content: str):
    content = BeautifulSoup(content, "html.parser")
    fullname = content.find("span", id="lbl_host").text
    ip = content.find("span", id="lbl_latlontrab").text
    return {"fullname": fullname, "ip": ip}


def get_date_info(content: str):
    content = BeautifulSoup(content, "html.parser")
    date = content.find("span", id="lblDateToday").text
    time = content.find("span", id="lblTime").text
    return {"date": date, "time": time}

def get_error_message(content: str) -> Optional[str]:
    """Extract error message from HTML content if present."""
    soup = BeautifulSoup(content, "html.parser")
    raw_error_span = soup.find("span", id="lbl_mensaje")
    error_span = raw_error_span.text.strip().lower() if raw_error_span else None
    if error_span and error_span not in ["&nbsp;", "label", ""]:
        return error_span

    return None



def extract_attendance_data(html_content: str) -> Optional[Dict[str, str]]:
    """Extract attendance data from HTML response."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Encontrar la tabla con los datos
        table = soup.find('table', class_='table table-condensed')
        if not table:
            return None
        
        # Extraer datos de las filas
        data = {}
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                data[key] = value
        
        # Mapear a nombres más limpios
        return {
            'empresa': data.get('Empresa', ''),
            'rut_empresa': data.get('Rut', ''),
            'direccion': data.get('Dirección', ''),  # Nota: encoding issue
            'nombre': data.get('Nombre', ''),
            'rut_empleado': list(data.values())[4] if len(data) > 4 else '',  # Segundo Rut
            'fecha': data.get('Fecha', ''),
            'hora': data.get('Hora', ''),
            'opcion': data.get('OpciÃ³n', ''),
            'latitud': data.get('Latitud Registrada', ''),
            'longitud': data.get('Longitud Registrada', ''),
            'codigo_hash': data.get('Codigo Hash', '')
        }
        
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None
