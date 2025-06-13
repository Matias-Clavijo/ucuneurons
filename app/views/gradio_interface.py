import gradio as gr
import pandas as pd
import requests
import json
from typing import Dict, Any
import base64
from io import BytesIO

class GradioInterface:
    """Vista de Gradio que se comunica con la API Flask"""
    
    def __init__(self, api_base_url: str = "http://localhost:5001", session_id: str = None):
        self.api_base_url = api_base_url
        self.session_id = session_id
        self.interface = None

    def _call_api(
        self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Método auxiliar para llamar a la API"""
        try:
            url = f"{self.api_base_url}{endpoint}"

            if method == "GET":
                response = requests.get(url, timeout=300)  # 5 minutos timeout
            elif method == "POST":
                response = requests.post(url, json=data, timeout=300)  # 5 minutos timeout
            else:
                return {"status": "error", "message": f"Método {method} no soportado"}

            return response.json()

        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": f"No se puede conectar a la API Flask. Verifica que esté corriendo en {self.api_base_url}.",
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error", 
                "message": f"Timeout: La API tardó más de 5 minutos en responder. El análisis de 12 requests al LLM puede requerir más tiempo."
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Error de request: {str(e)}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Error inesperado: {str(e)}"}
    
    def list_to_message(self, list: list) -> str:
        return '\n'.join(f"- {item}" for item in list)

    def process_text_interface(self, chemicals, place, quentity_input, materials, frequency, environment, additional_info, process, image_pil) -> str:

        required_fields = {
            "Chemicals": chemicals,
            "Place": place,
            "Materials": materials,
            "Frequency of use": frequency,
            "Environment": environment,
            "Process": process,
        }
        empty_fields = [name for name, value in required_fields.items() if not str(value).strip()]

        if empty_fields:
            missing_fields_str = ", ".join(empty_fields)
            return f"❌ Please fill in all required fields. Missing: {missing_fields_str}."

        payload = {
            "chemicals": chemicals,
            "place": place,
            "materials": materials,
            "frequency_of_use": frequency,
            "environment": environment,
            "process": process,
            "additional_info": additional_info,
        }

        if image_pil:
            buffered = BytesIO()
            image_pil.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            payload['image'] = img_str

        print("Sending payload to API:", payload)
        
        # Preparar datos para el endpoint analyze-multi-field
        npt_api_payload = {
            "chemical_name": chemicals,
            "temperature": "No proporcionada",  # Puedes agregar un campo para esto
            "requests_per_field": 3,
            "fields": ["procedimiento_trabajo", "proteccion_colectiva", "factor_vla", "volatilidad", "frases_h"]
        }
        
        print(f"🚀 Calling API endpoint: /api/rag-faiss/analyze-multi-field")
        print(f"📦 API payload: {npt_api_payload}")
        
        try:
            result_recomendations = self._call_api(f"/risk-chat/{self.session_id}/analyze", "POST", {"data": payload})
            result_recomendations = result_recomendations.get("chat_response", {})
            print(f"✅ API response received: {result_recomendations}")
            
        except Exception as e:
            print(f"❌ Error calling API: {str(e)}")
            return f"❌ **Error llamando a la API:** {str(e)}"

        # Siempre convertir el resultado a string para evitar errores de Gradio
        try:
            
            return f"""
              ## Riesgo estimado calculo NTP: Altoss
        #  \n ### Consideraciones para el operador: \n {self.list_to_message(result_recomendations.get("operators_risk_message", []))}
        #  \n ### Requerimientos de protección: \n  {self.list_to_message(result_recomendations.get("operator_requirements", []))}
        #  \n ### Consideraciones para el ambiente: \n  {self.list_to_message(result_recomendations.get("environment_risk_message", []))}"""
        except Exception as e:
            return f"❌ **Error procesando respuesta:** {str(e)}\n\n**Respuesta raw:**\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```"

    def create_interface(self) -> gr.Blocks:
        """Crear la interfaz de Gradio"""

        with gr.Blocks(
            title="Ucuneurons",
            theme=gr.themes.Base()
        ) as interface:
            
            gr.Markdown("# 🚀 Ucuneurons")
            
            # Tab 1: Procesador de Texto
            with gr.Tab("📝 Environmental Health and Safety Professionals Optimizer"):
                gr.Markdown("### Complete the form")
                
                with gr.Row():
                    with gr.Column():
                        chemicals_input = gr.Textbox(
                            label="Chemicals",
                            placeholder="Write the chemicals that are involved (Ej: Pentanol)"
                        )
                        quentity_input = gr.Textbox(
                            label="Quantity",
                            placeholder="Write the quantity of the materials that are involved (Ej: 100 mg/m3)"
                        )
                        place_input = gr.Textbox(
                            label="Place",
                            placeholder="Write the place of the factory (Ej: Planta 1 Rosario, Argentina)"
                        )
                        materials_input = gr.Textbox(
                            label="Materials",
                            placeholder="Write the materials that are involved (Ej: Bomb)"
                        )
                        gr.Image(value="app/image/image.jpeg", interactive=False, label="Tabla de frecuencia de uso", width=400, height=300)
                        frequency_of_use_input = gr.Slider(
                            minimum=0,
                            maximum=4,
                            step=1,            
                            label="Class of frequency of use"
                        )
                        environment_input = gr.Textbox(
                            label="Environment",
                            placeholder="Is indoor or outdoor (you can specified wheather)"
                        )
                        process_input = gr.Textbox(
                            label="Process",
                            placeholder="Write the process to do (Ej: Move 3 feets)",
                            lines=4
                        )
                        additional_info_input = gr.Textbox(
                            label="Additional information",
                            placeholder="You can specify additional information that you think is important",
                            lines=4
                        )

                        process_btn = gr.Button("🔄 Process", variant="primary")
                    
                    with gr.Column():
                        image_input = gr.Image(label="Image", type="pil")
                        process_output = gr.Markdown(
                            label="Result",
                            value="Ingresa texto y presiona 'Procesar Texto'"
                        )

                process_btn.click(
                    fn=self.process_text_interface,
                    inputs=[
                        chemicals_input,
                        place_input,
                        quentity_input,
                        materials_input,
                        frequency_of_use_input,
                        environment_input,
                        additional_info_input,
                        process_input,
                        image_input
                    ],
                    outputs=process_output
                )

        self.interface = interface
        return interface

    def launch(self, **kwargs):
        """Lanzar la interfaz"""
        if not self.interface:
            self.create_interface()

        return self.interface.launch(**kwargs)
