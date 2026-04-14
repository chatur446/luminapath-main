import requests

# Real OCT scan from public medical dataset
url = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Retinal_OCT_scan.jpg/800px-Retinal_OCT_scan.jpg"

response = requests.get(url)
with open(r"C:\Users\a\Desktop\luminapath-main\static\uploaded_images\real_oct.jpg", "wb") as f:
    f.write(response.content)

print("Downloaded successfully!")