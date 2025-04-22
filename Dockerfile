# বেস ইমেজ হিসেবে একটি অফিসিয়াল পাইথন রানটাইম ব্যবহার করুন
FROM python:3.9-slim

# ওয়ার্কিং ডিরেক্টরি সেট করুন
WORKDIR /app

# requirements.txt কপি করুন এবং ইনস্টল করুন
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# অ্যাপ্লিকেশনের কোড কপি করুন
COPY app.py /app/

# Render সাধারণত PORT এনভায়রনমেন্ট ভেরিয়েবল সেট করে।
# Gunicorn এটি ব্যবহার করবে। এখানে EXPOSE না করলেও চলে, কারণ gunicorn নিজেই PORT ভেরিয়েবল থেকে পোর্ট নেয়।
# তবে ডকুমেন্টেশনের জন্য রাখা যেতে পারে। Render মূলত PORT ভেরিয়েবলের ওপর নির্ভর করে।
# EXPOSE 8080 # অথবা Render যে পোর্ট দেয় (যেমন 10000)

# Gunicorn ব্যবহার করে অ্যাপ রান করার কমান্ড
# Render স্বয়ংক্রিয়ভাবে PORT এনভায়রনমেন্ট ভেরিয়েবল সেট করবে।
# Gunicorn এটিকে বাইন্ড করার জন্য ব্যবহার করবে।
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
