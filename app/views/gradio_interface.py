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
    
    def _call_api(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Método auxiliar para llamar a la API"""
        try:
            url = f"{self.api_base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            else:
                return {"status": "error", "message": f"Método {method} no soportado"}
            
            return response.json()
            
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "No se puede conectar a la API Flask. Verifica que esté corriendo en el puerto 5000."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_to_message(self, list: list) -> str:
        return '\n'.join(f"- {item}" for item in list)
    
    def process_text_interface(self, chemicals, place, materials, frequency, environment, additional_info, process, image_pil) -> str:
        
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
        result = self._call_api(f"/risk-chat/{self.session_id}/analyze", "POST", {"data": payload})

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        chat_result = result.get("chat_response", {})
        # ntp_result = chat_result.get("npt_risk_data", {})
        # return f"""
        
        #     ## Riesgo del operador (IN): {ntp_result.get("risk", "")}
        #  \n ### Consideraciones para el operador: \n {self.list_to_message(chat_result.get("operators_risk_message", []))}
        #  \n ### Requerimientos de protección: \n  {self.list_to_message(chat_result.get("operator_requirements", []))}
        #  \n ## Riesgo estimado del ambiente: {chat_result.get("environment_risk_level", "")} \n
        #  \n ### Consideraciones para el ambiente: \n  {self.list_to_message(chat_result.get("environment_risk_message", []))}

        # \n\n\n

        # Extra info : {ntp_result}
        # """
        return chat_result
          
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
                        materials_input = gr.Textbox(
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
                        frequency_of_use_input = gr.Textbox(
                            label="Frequency of use",
                            placeholder="Specify the frequency in which the operator repeats the process (Ej: 10 times a day)"
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