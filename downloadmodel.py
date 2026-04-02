from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "ai4bharat/indictrans2-indic-en-1B"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)

print("Model downloaded successfully")