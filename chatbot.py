import re
import json
from datetime import datetime
from chemical_database import CHEMICAL_DATABASE, calculate_reagent
from models import ChatMessage, Calculation, Experiment, ActivityLog

class LabMateChatbot:
    def __init__(self):
        self.knowledge_base = {
            'greetings': [
                'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'
            ],
            'calculations': [
                'calculate', 'how much', 'mass', 'molarity', 'volume', 'concentration'
            ],
            'chemicals': [
                'chemical', 'reagent', 'compound', 'substance', 'molecule'
            ],
            'safety': [
                'safety', 'hazard', 'dangerous', 'toxic', 'corrosive', 'flammable'
            ],
            'experiments': [
                'experiment', 'procedure', 'protocol', 'method', 'lab work'
            ],
            'help': [
                'help', 'what can you do', 'assist', 'support', 'guide'
            ]
        }
        
        self.responses = {
            'greeting': [
                "Hello! I'm LabMate AI, your intelligent laboratory assistant. How can I help you today?",
                "Hi there! I'm here to assist you with laboratory calculations, chemical information, and safety guidance.",
                "Welcome! I can help you with chemical calculations, MSDS lookups, experiment planning, and safety protocols."
            ],
            'calculation_help': [
                "I can help you calculate reagent masses for specific molarities and volumes. Just tell me the chemical name, desired molarity, and volume.",
                "For calculations, I need: 1) Chemical name, 2) Desired molarity (M), 3) Volume (mL). Example: 'Calculate 0.1M NaCl for 100mL'"
            ],
            'chemical_info': [
                "I have information about common laboratory chemicals including their formulas, molar masses, and safety hazards.",
                "You can ask me about chemical properties, safety information, or search for specific compounds in our database."
            ],
            'safety_info': [
                "I can provide safety information about chemicals, including hazard classifications and handling precautions.",
                "Always follow proper safety protocols when working with chemicals. I can help you identify potential hazards."
            ],
            'experiment_help': [
                "I can help you plan experiments, suggest procedures, and provide guidance on laboratory techniques.",
                "Tell me about your experiment goals and I can help you design a safe and effective procedure."
            ],
            'default': [
                "I'm not sure I understand. Could you rephrase your question? I can help with calculations, chemical information, safety, or experiments.",
                "I'm here to help with laboratory-related questions. Try asking about calculations, chemicals, safety, or experiments."
            ]
        }

    def process_message(self, message, user_id, db_session):
        """Process user message and generate appropriate response"""
        message_lower = message.lower()
        
        # Determine intent
        intent = self._classify_intent(message_lower)
        
        # Generate response based on intent
        if intent == 'calculation':
            return self._handle_calculation(message, user_id, db_session)
        elif intent == 'chemical_info':
            return self._handle_chemical_info(message, user_id, db_session)
        elif intent == 'safety':
            return self._handle_safety_info(message, user_id, db_session)
        elif intent == 'experiment':
            return self._handle_experiment_help(message, user_id, db_session)
        elif intent == 'greeting':
            return self._get_random_response('greeting')
        elif intent == 'help':
            return self._handle_help_request()
        else:
            return self._get_random_response('default')

    def _classify_intent(self, message):
        """Classify user intent based on keywords"""
        for intent, keywords in self.knowledge_base.items():
            if any(keyword in message for keyword in keywords):
                return intent
        return 'default'

    def _handle_calculation(self, message, user_id, db_session):
        """Handle calculation requests"""
        # Extract chemical name, molarity, and volume from message
        chemical_match = None
        molarity_match = None
        volume_match = None
        
        # Look for chemical names in the database
        for chemical in CHEMICAL_DATABASE.keys():
            if chemical.lower() in message.lower():
                chemical_match = chemical
                break
        
        # Look for molarity (e.g., "0.1M", "0.1 M", "0.1 molar")
        molarity_pattern = r'(\d+\.?\d*)\s*M(?:olar)?'
        molarity_match = re.search(molarity_pattern, message)
        
        # Look for volume (e.g., "100mL", "100 mL", "100ml")
        volume_pattern = r'(\d+\.?\d*)\s*mL?'
        volume_match = re.search(volume_pattern, message)
        
        if chemical_match and molarity_match and volume_match:
            try:
                molarity = float(molarity_match.group(1))
                volume = float(volume_match.group(1))
                
                result = calculate_reagent(chemical_match, molarity, volume)
                
                if 'error' not in result:
                    # Save calculation to database
                    calculation = Calculation(
                        user_id=user_id,
                        reagent=chemical_match,
                        formula=result['formula'],
                        molarity=molarity,
                        volume=volume,
                        mass_needed=result['mass_needed']
                    )
                    db_session.add(calculation)
                    db_session.commit()
                    
                    response = f"✅ **Calculation Complete!**\n\n"
                    response += f"**Chemical:** {chemical_match} ({result['formula']})\n"
                    response += f"**Molarity:** {molarity} M\n"
                    response += f"**Volume:** {volume} mL\n"
                    response += f"**Mass needed:** {result['mass_needed']:.4f} g\n\n"
                    response += f"**Instructions:** {result['instructions']}"
                    
                    return response
                else:
                    return f"❌ Error: {result['error']}"
            except ValueError:
                return "❌ I couldn't parse the numbers. Please use format like '0.1M' and '100mL'."
        else:
            missing = []
            if not chemical_match:
                missing.append("chemical name")
            if not molarity_match:
                missing.append("molarity (e.g., 0.1M)")
            if not volume_match:
                missing.append("volume (e.g., 100mL)")
            
            return f"❌ I need more information. Please specify: {', '.join(missing)}.\n\nExample: 'Calculate 0.1M NaCl for 100mL'"

    def _handle_chemical_info(self, message, user_id, db_session):
        """Handle chemical information requests"""
        # Look for chemical names in the database
        found_chemicals = []
        for chemical in CHEMICAL_DATABASE.keys():
            if chemical.lower() in message.lower():
                found_chemicals.append(chemical)
        
        if found_chemicals:
            response = "🧪 **Chemical Information:**\n\n"
            for chemical in found_chemicals[:3]:  # Limit to 3 chemicals
                data = CHEMICAL_DATABASE[chemical]
                response += f"**{chemical}** ({data['formula']})\n"
                response += f"• Molar Mass: {data['molar_mass']} g/mol\n"
                response += f"• Hazards: {', '.join(data['hazards'])}\n"
                response += f"• Description: {data['description']}\n\n"
            
            if len(found_chemicals) > 3:
                response += f"... and {len(found_chemicals) - 3} more chemicals found."
            
            return response
        else:
            return "❌ I couldn't find that chemical in my database. Available chemicals include: " + ", ".join(list(CHEMICAL_DATABASE.keys())[:5]) + "..."

    def _handle_safety_info(self, message, user_id, db_session):
        """Handle safety information requests"""
        # Look for specific chemical safety info
        for chemical in CHEMICAL_DATABASE.keys():
            if chemical.lower() in message.lower():
                data = CHEMICAL_DATABASE[chemical]
                response = f"⚠️ **Safety Information for {chemical}:**\n\n"
                response += f"**Hazards:** {', '.join(data['hazards'])}\n\n"
                
                if 'Corrosive' in data['hazards']:
                    response += "• Wear protective gloves and eye protection\n"
                    response += "• Work in a fume hood if possible\n"
                if 'Flammable' in data['hazards']:
                    response += "• Keep away from heat sources and open flames\n"
                    response += "• Store in a cool, well-ventilated area\n"
                if 'Toxic' in data['hazards']:
                    response += "• Avoid inhalation and skin contact\n"
                    response += "• Use in well-ventilated area\n"
                if 'Oxidizer' in data['hazards']:
                    response += "• Keep away from flammable materials\n"
                    response += "• Store separately from reducing agents\n"
                
                return response
        
        # General safety advice
        return "⚠️ **General Laboratory Safety Tips:**\n\n" \
               "• Always wear appropriate PPE (gloves, goggles, lab coat)\n" \
               "• Work in well-ventilated areas or fume hoods\n" \
               "• Never eat, drink, or smoke in the laboratory\n" \
               "• Know the location of safety equipment (eyewash, shower, fire extinguisher)\n" \
               "• Read MSDS sheets before using any chemical\n" \
               "• Dispose of chemicals according to regulations\n\n" \
               "Ask me about specific chemical safety information!"

    def _handle_experiment_help(self, message, user_id, db_session):
        """Handle experiment-related questions"""
        return "🧪 **Experiment Planning Assistance:**\n\n" \
               "I can help you with:\n" \
               "• Designing experimental procedures\n" \
               "• Calculating reagent amounts\n" \
               "• Safety considerations\n" \
               "• Equipment recommendations\n" \
               "• Data analysis guidance\n\n" \
               "Tell me about your experiment goals and I'll provide specific guidance!"

    def _handle_help_request(self):
        """Handle help requests"""
        return "🤖 **LabMate AI - What I Can Do:**\n\n" \
               "**Calculations:**\n" \
               "• Calculate reagent masses for specific concentrations\n" \
               "• Example: 'Calculate 0.1M NaCl for 100mL'\n\n" \
               "**Chemical Information:**\n" \
               "• Look up chemical properties and safety data\n" \
               "• Example: 'Tell me about sodium hydroxide'\n\n" \
               "**Safety Guidance:**\n" \
               "• Get safety information for specific chemicals\n" \
               "• Example: 'Safety info for sulfuric acid'\n\n" \
               "**Experiment Help:**\n" \
               "• Plan experiments and procedures\n" \
               "• Example: 'Help me plan a titration experiment'\n\n" \
               "Just ask me anything about laboratory work!"

    def _get_random_response(self, response_type):
        """Get a random response from the specified type"""
        import random
        responses = self.responses.get(response_type, self.responses['default'])
        return random.choice(responses)

    def save_conversation(self, user_id, user_message, bot_response, db_session):
        """Save conversation to database"""
        # Save user message
        user_msg = ChatMessage(
            user_id=user_id,
            message=user_message,
            response="",  # User messages don't have responses
            is_user_message=True
        )
        db_session.add(user_msg)
        
        # Save bot response
        bot_msg = ChatMessage(
            user_id=user_id,
            message="",  # Bot responses don't have user messages
            response=bot_response,
            is_user_message=False
        )
        db_session.add(bot_msg)
        
        db_session.commit()

# Global chatbot instance
chatbot = LabMateChatbot()
