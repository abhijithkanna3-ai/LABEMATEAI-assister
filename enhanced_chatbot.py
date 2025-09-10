import re
import json
import os
from datetime import datetime
from chemical_database import CHEMICAL_DATABASE, calculate_reagent
try:
    from models import ChatMessage, Calculation, Experiment, ActivityLog
except ImportError:
    # Fallback for testing
    print("Warning: Could not import models. Some features may not work.")
    ChatMessage = None
    Calculation = None
    Experiment = None
    ActivityLog = None
import google.generativeai as genai

class EnhancedLabMateChatbot:
    def __init__(self):
        # Initialize Gemini API for all responses
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyCeo5U96gMxO1h248cPdLG46l-wWQbQQUU')
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.use_gemini = True
                # print("✅ Gemini API initialized successfully!")
            except Exception as e:
                # print(f"❌ Error initializing Gemini API: {e}")
                self.use_gemini = False
        else:
            self.use_gemini = False
            # print("Warning: GEMINI_API_KEY not found. Using fallback responses.")
        
        
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

    def process_message(self, message, user_id, db_session):
        """Process user message and generate appropriate response"""
        try:
            # print(f"Processing message: {message} for user: {user_id}")
            
            # Get user context (experiments, calculations, activities)
            user_context = self._get_user_context(user_id, db_session)
            # print(f"User context retrieved: {len(user_context.get('experiments', []))} experiments")
            
            if self.use_gemini:
                # print("Using Gemini API for response")
                # Use Gemini for intelligent responses
                response = self._generate_gemini_response(message, user_context)
            else:
                # print("Using fallback response system")
                # Fallback to rule-based responses
                response = self._generate_fallback_response(message, user_id, db_session)
            
            # print(f"Generated response: {response[:100]}...")
            return response
            
        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return "I apologize, but I encountered an error processing your message. Please try again."


    def _get_user_context(self, user_id, db_session):
        """Get user's experiment history, calculations, and activities for context"""
        try:
            # Check if models are available
            if not Experiment or not Calculation or not ActivityLog:
                return {'experiments': [], 'calculations': [], 'activities': []}
            
            # Get recent experiments
            recent_experiments = Experiment.query.filter_by(user_id=user_id).order_by(Experiment.created_at.desc()).limit(5).all()
            
            # Get recent calculations
            recent_calculations = Calculation.query.filter_by(user_id=user_id).order_by(Calculation.created_at.desc()).limit(10).all()
            
            # Get recent activities
            recent_activities = ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(10).all()
            
            context = {
                'experiments': [],
                'calculations': [],
                'activities': []
            }
            
            # Format experiments
            for exp in recent_experiments:
                context['experiments'].append({
                    'title': exp.title,
                    'description': exp.description,
                    'procedures': exp.procedures,
                    'observations': exp.observations,
                    'results': exp.results,
                    'date': exp.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            # Format calculations
            for calc in recent_calculations:
                context['calculations'].append({
                    'reagent': calc.reagent,
                    'formula': calc.formula,
                    'molarity': calc.molarity,
                    'volume': calc.volume,
                    'mass_needed': calc.mass_needed,
                    'date': calc.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            # Format activities
            for activity in recent_activities:
                context['activities'].append({
                    'action_type': activity.action_type,
                    'description': activity.description,
                    'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M')
                })
            
            return context
            
        except Exception as e:
            print(f"Error getting user context: {e}")
            return {'experiments': [], 'calculations': [], 'activities': []}

    def _generate_gemini_response(self, message, user_context):
        """Generate response using Gemini API with user context"""
        try:
            # Create context-aware prompt
            prompt = self._create_context_prompt(message, user_context)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Process the response
            if response and response.text:
                return self._format_gemini_response(response.text)
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            return "I'm having trouble connecting to my AI service. Let me help you with a basic response."

    def _create_context_prompt(self, message, user_context):
        """Create a context-aware prompt for Gemini"""
        prompt = f"""You are LabMate AI, an intelligent laboratory assistant for chemistry and laboratory work. You can answer both general chemistry questions and provide personalized assistance based on the user's experiment history.

USER'S RECENT EXPERIMENTS:
{json.dumps(user_context['experiments'], indent=2)}

USER'S RECENT CALCULATIONS:
{json.dumps(user_context['calculations'], indent=2)}

USER'S RECENT ACTIVITIES:
{json.dumps(user_context['activities'], indent=2)}

AVAILABLE CHEMICALS DATABASE:
{json.dumps(list(CHEMICAL_DATABASE.keys()), indent=2)}

USER MESSAGE: {message}

INSTRUCTIONS:
1. **Answer ALL types of chemistry and laboratory questions** - general questions, specific problems, calculations, safety, procedures, etc.
2. **Use your general chemistry knowledge** to answer questions even if not related to the user's history
3. **Reference the user's experiment history ONLY when relevant** to provide personalized insights
4. **Provide comprehensive answers** for general chemistry questions like:
   - Chemical properties and reactions
   - Laboratory techniques and procedures
   - Safety guidelines and precautions
   - Calculations and formulas
   - Equipment usage and maintenance
   - Experimental design and troubleshooting
5. **Be conversational and supportive** in all responses
6. **Format your response with proper markdown** (use **bold** for emphasis)
7. **Keep responses informative but concise**
8. **Always prioritize safety** in your recommendations
9. **If performing calculations, show steps and results**
10. **If the question is general chemistry, answer it fully** - don't limit yourself to just the user's history

Examples of what you should answer:
- "What is the difference between ionic and covalent bonds?"
- "How do I prepare a 0.1M solution of sodium chloride?"
- "What safety precautions should I take when working with acids?"
- "Explain the process of titration"
- "What is the molecular structure of benzene?"
- "How do I calculate pH of a solution?"

Respond as LabMate AI:"""

        return prompt

    def _format_gemini_response(self, response_text):
        """Format Gemini response for display"""
        # Clean up the response
        formatted = response_text.strip()
        
        # Ensure proper formatting
        if not formatted.startswith('**') and not formatted.startswith('LabMate AI'):
            formatted = f"**LabMate AI:** {formatted}"
        
        return formatted

    def _generate_fallback_response(self, message, user_id, db_session):
        """Generate fallback response using rule-based system"""
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
            # For general questions, provide a helpful response
            return self._handle_general_question(message)

    def _handle_general_question(self, message):
        """Handle general chemistry and laboratory questions"""
        message_lower = message.lower()
        
        # Common chemistry topics
        if any(word in message_lower for word in ['bond', 'ionic', 'covalent', 'molecular']):
            return "🔬 **Chemical Bonds:**\n\n" \
                   "**Ionic Bonds:**\n" \
                   "• Formed between metals and non-metals\n" \
                   "• Electrons are transferred completely\n" \
                   "• Example: NaCl (sodium chloride)\n\n" \
                   "**Covalent Bonds:**\n" \
                   "• Formed between non-metals\n" \
                   "• Electrons are shared\n" \
                   "• Example: H₂O (water)\n\n" \
                   "Would you like me to explain more about specific types of bonds?"
        
        elif any(word in message_lower for word in ['ph', 'acid', 'base', 'alkaline']):
            return "🧪 **pH and Acids/Bases:**\n\n" \
                   "**pH Scale:**\n" \
                   "• 0-6: Acidic\n" \
                   "• 7: Neutral\n" \
                   "• 8-14: Basic/Alkaline\n\n" \
                   "**pH Calculation:**\n" \
                   "• pH = -log[H⁺]\n" \
                   "• pOH = -log[OH⁻]\n" \
                   "• pH + pOH = 14\n\n" \
                   "**Safety:** Always add acid to water, never water to acid!"
        
        elif any(word in message_lower for word in ['titration', 'indicator', 'endpoint']):
            return "⚗️ **Titration Process:**\n\n" \
                   "**Steps:**\n" \
                   "1. Prepare standard solution\n" \
                   "2. Add indicator\n" \
                   "3. Slowly add titrant\n" \
                   "4. Observe color change at endpoint\n" \
                   "5. Calculate concentration\n\n" \
                   "**Common Indicators:**\n" \
                   "• Phenolphthalein (pink in base)\n" \
                   "• Methyl orange (red in acid)\n\n" \
                   "Need help with a specific titration calculation?"
        
        else:
            return "🤔 **I'd be happy to help with that!**\n\n" \
                   "I can assist with:\n" \
                   "• Chemistry concepts and reactions\n" \
                   "• Laboratory procedures and techniques\n" \
                   "• Safety guidelines and precautions\n" \
                   "• Calculations and formulas\n" \
                   "• Equipment usage\n\n" \
                   "Could you be more specific about what you'd like to know? I'm here to help with any chemistry or laboratory question!"

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
        gemini_status = "✅ Gemini AI" if self.use_gemini else "❌ Gemini AI (Not Available)"
        
        return f"🤖 **LabMate AI - What I Can Do:**\n\n" \
               f"**AI Services:**\n" \
               f"• {gemini_status} - Intelligent chemistry and laboratory assistance\n" \
               f"• Fallback system - Basic rule-based responses\n\n" \
               "**Chemistry & Laboratory Questions:**\n" \
               "• Answer any chemistry or laboratory question\n" \
               "• Explain concepts, reactions, and procedures\n" \
               "• Advanced chemical reactions and mechanisms\n" \
               "• Laboratory procedures and techniques\n" \
               "• Safety protocols and chemical hazards\n" \
               "• Complex calculations and formulas\n" \
               "• Example: 'Explain the mechanism of SN2 reactions'\n\n" \
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
               "**Your History:**\n" \
               "• Discuss your past experiments and calculations\n" \
               "• Get insights from your lab work\n\n" \
               "**I can answer ANY chemistry or laboratory question!** Just ask me anything!"

    def _get_random_response(self, response_type):
        """Get a random response from the specified type"""
        import random
        responses = {
            'greeting': [
                "Hello! I'm LabMate AI, your intelligent laboratory assistant. How can I help you today?",
                "Hi there! I'm here to assist you with laboratory calculations, chemical information, and safety guidance.",
                "Welcome! I can help you with chemical calculations, MSDS lookups, experiment planning, and safety protocols."
            ],
            'default': [
                "I'm not sure I understand. Could you rephrase your question? I can help with calculations, chemical information, safety, or experiments.",
                "I'm here to help with laboratory-related questions. Try asking about calculations, chemicals, safety, or experiments."
            ]
        }
        response_list = responses.get(response_type, responses['default'])
        return random.choice(response_list)

    def save_conversation(self, user_id, user_message, bot_response, db_session):
        """Save conversation to database"""
        try:
            if not ChatMessage:
                print("ChatMessage model not available, skipping save")
                return
            
            # Check if db_session has add method
            if not hasattr(db_session, 'add'):
                print("Database session not available, skipping save")
                return
                
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
            # print("Conversation saved successfully")
        except Exception as e:
            # print(f"Error saving conversation: {e}")
            # import traceback
            # traceback.print_exc()
            try:
                if hasattr(db_session, 'rollback'):
                    db_session.rollback()
            except:
                pass

# Global enhanced chatbot instance
enhanced_chatbot = EnhancedLabMateChatbot()
