import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load model and tokenizer
model_name = "AI4Chem/ChemLLM-7B-Chat-1.5-DPO"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    device_map="auto",
    trust_remote_code=True,
    low_cpu_mem_usage=True
)

# Test simple generation
prompt = "What is the molecular formula of water?"
inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

print("Input shape:", inputs['input_ids'].shape)
print("Input IDs:", inputs['input_ids'])

# Generate
with torch.no_grad():
    outputs = model.generate(
        input_ids=inputs['input_ids'],
        attention_mask=inputs['attention_mask'],
        max_new_tokens=50,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

print("Output type:", type(outputs))
print("Output length:", len(outputs))
print("First output type:", type(outputs[0]))
print("First output shape:", outputs[0].shape if hasattr(outputs[0], 'shape') else 'No shape')

# Decode
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("Response:", response)


