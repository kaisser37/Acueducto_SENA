from fastapi import FastAPI, Request, Depends, HTTPException, Cookie, Response, Form, status, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from models import Documento, Usuario, Empresa
from funciones import *
from str_aleatorio import generar_random_id
import bcrypt
from docx import Document  # Importar para manejar archivos DOCX
from reportlab.lib.pagesizes import letter  # Importar para manejar páginas
from reportlab.pdfgen import canvas  # Importar para generar PDFs

SUPER_ADMIN = "SuperAdmin"
ADMIN = "Admin"
datos_usuario = None

app = FastAPI()

# Agregando los archivos estáticos que están en la carpeta dist del proyecto
app.mount("/static", StaticFiles(directory="public/dist"), name="static")

template = Jinja2Templates(directory="public/templates")

def docx_to_pdf(docx_path, pdf_path):
    # Cargar el archivo DOCX
    doc = Document(docx_path)

    # Crear un PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Posición inicial
    y = height - 40  # Iniciar desde la parte superior

    # Leer el contenido del DOCX y escribirlo en el PDF
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:  # Solo agregar si hay texto
            c.drawString(40, y, text)
            y -= 12  # Mover hacia abajo para la próxima línea
            if y < 40:  # Si alcanzamos el fondo de la página
                c.showPage()  # Crear una nueva página
                y = height - 40  # Restablecer posición

    c.save()

def manejarDocumentos(nombre_documento, datos, nit, id_usuario, db, id_servicio):
    archivo = 'public/dist/ArchivosDescarga/' + nombre_documento + '.docx'
    
    # Modificar el documento
    documento_modificado = reemplazar_texto(archivo, datos)
    docx_path = f'public/dist/ArchivosDescarga/Generados/{nombre_documento}_Editado_{nit}.docx'
    documento_modificado.save(docx_path)

    # Convertir a PDF
    archivo_pdf = f'public/dist/ArchivosDescarga/Generados/{nombre_documento}_{nit}.pdf'
    try:
        docx_to_pdf(docx_path, archivo_pdf)  # Convertir usando la nueva función
    except Exception as e:
        print("Error al convertir a PDF:", e)
        raise HTTPException(status_code=500, detail="Error al convertir el documento a PDF.")

    nuevo_documento1 = Documento(
        id_usuario=id_usuario,
        nom_doc=f'{nombre_documento}_{nit}',
        id_servicio=id_servicio,
        tipo='pdf',
        url=f'ArchivosDescarga/Generados/{nombre_documento}_{nit}.pdf'
    )

    db.add(nuevo_documento1)
    db.commit()
    db.refresh(nuevo_documento1)

def generarDocx(
    request: Request, 
    token: str, 
    db: Session,
    nit: str,
    presidente: str,
    patrimonio: str,
    municipio: str,
    departamento: str,
    web: str,
    horario: str,
    sigla: str,
    vereda: str,
    fecha: str,
    especificaciones: str,
    diametro: str,
    caudal_permanente: str,
    rango_medicion: str
):
    if token:
        is_token_valid = verificar_token(token, db)

        if is_token_valid:
            rol_usuario = get_rol(is_token_valid, db)
            print(rol_usuario)
            headers = elimimar_cache()
            datos_usuario = get_datos_usuario(is_token_valid, db)

            if rol_usuario == ADMIN:
                # Eliminar documentos asociados al usuario
                documentos_a_eliminar = db.query(Documento).filter(Documento.id_usuario == is_token_valid).all()
                for documento in documentos_a_eliminar:
                    db.delete(documento)
                db.commit()    
                id_usuario = is_token_valid

                # Obtener información del usuario y su empresa
                usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
                if usuario:
                    empresa = db.query(Empresa).filter(Empresa.id_empresa == usuario.empresa).first()
                    if empresa:
                        print(f'ID del Usuario: {usuario.id_usuario}')
                        print(f'Nombre del Usuario: {usuario.nom_usuario}')
                        print(f'Empresa del Usuario:')
                        print(f'  - ID: {empresa.id_empresa}')
                        print(f'  - Nombre: {empresa.nom_empresa}')

                        datos = {
                            '[Nombre de la Asociación]': empresa.nom_empresa,
                            '[Campo NIT]': nit,
                            '[Presidente Asociacion]': presidente,
                            '[Campo Patrimonio]': patrimonio,
                            '[Campo Dirección]': empresa.direccion_empresa,
                            '[Campo Municipio]': municipio,
                            '[Campo Departamento]': departamento,
                            '[Campo Teléfonos]': "Celular: " + empresa.tel_cel + " Telefono: " + empresa.tel_fijo,
                            '[Campo Página Web]': web,
                            '[Campo Correo]': empresa.email,
                            '[Campo Horario Atención]': horario,
                            '[SIGLA]': sigla,
                            '[Dirección]': empresa.direccion_empresa,
                            '[Vereda]': vereda,
                            '[Municipio]': municipio,
                            '[Departamento]': departamento,
                            '[Fecha de Constitución]': fecha,
                            '[Campo Especificaiones]': especificaciones,
                            '[Campo Diametro]': diametro,
                            '[Campo Caudal Permanente]': caudal_permanente,
                            '[Campo Rango Medicion]': rango_medicion,
                        }
                        
                        arreglo_rutas = []
                        # Crear, guardar y convertir a PDF archivo 1
                        manejarDocumentos("P01-F-03_Estatutos_Asociacion_Suscriptores", datos, nit, id_usuario, db, 1)
                        arreglo_rutas.append(f'ArchivosDescarga/Generados/P01-F-03_Estatutos_Asociacion_Suscriptores_{nit}.pdf')
                        manejarDocumentos("P01-F-02_Formato_Contrato_Condiciones_Uniformes", datos, nit, id_usuario, db, 2)
                        arreglo_rutas.append(f'ArchivosDescarga/Generados/P01-F-02_Formato_Contrato_Condiciones_Uniformes_{nit}.pdf')

                        response = template.TemplateResponse(
                            "paso-1/paso1-1/generar_documentos.html", 
                            {"request": request, "usuario": datos_usuario, "rutas_pdf": arreglo_rutas}
                        )
                        response.headers.update(headers)  # Actualiza las cabeceras
                        return response
                    else:
                        print('El usuario no está asociado a ninguna empresa.')
                else:
                    print('No se encontró el usuario con el ID proporcionado.')

                response = template.TemplateResponse(
                    "paso-1/paso1-1/generar_documentos.html", 
                    {"request": request, "usuario": datos_usuario, "rutas_pdf": []}
                )
                response.headers.update(headers)  # Actualiza las cabeceras
                return response
            else:
                alerta = {
                    "mensaje": "No tiene los permisos para esta acción",
                    "color": "warning",
                }
                response = template.TemplateResponse(
                    "index.html", 
                    {"request": request, "alerta": alerta, "usuario": datos_usuario}
                )
                response.headers.update(headers)  # Actualiza las cabeceras
                return response
        else:
            return RedirectResponse(url="/", status_code=status.HTTP_403_FORBIDDEN)
    else:
        return RedirectResponse(url="/", status_code=status.HTTP_403_FORBIDDEN)
