import os
import requests
from flask import Flask, request, Response

app = Flask(__name__)

# Render সাধারণত 'PORT' এনভায়রনমেন্ট ভেরিয়েবলে পোর্ট সেট করে
# লোকাল টেস্টিং বা ডিফল্ট হিসেবে 8080 ব্যবহার করা যেতে পারে
port = int(os.environ.get("PORT", 8080))

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
    """
    ইনকামিং অনুরোধ গ্রহণ করে, ডেস্টিনেশন সার্ভারে পাঠায় এবং রেসপন্স ফেরত দেয়।
    """
    # গন্তব্য ইউআরএল তৈরি (শুধুমাত্র HTTP)
    # request.url রুট থেকে পুরো পাথসহ URL দেয় (e.g., http://your-render-app.com/http://example.com/page)
    # আমাদের প্রক্সি ব্যবহারের নিয়ম অনুযায়ী URL অনুরোধের পাথ হিসেবে আসবে
    # যেমন: GET http://example.com/ HTTP/1.1 এর পরিবর্তে GET / HTTP/1.1 Host: example.com
    # অথবা ক্লায়েন্টকে পুরো URL পাথ হিসেবে পাঠাতে হবে: GET /http://example.com/page HTTP/1.1

    # একটি সরল পদ্ধতি হলো Host হেডার ব্যবহার করা
    host = request.headers.get('Host')
    if not host:
        return "Host header is missing", 400

    # স্কিম নির্ধারণ (সরল প্রক্সির জন্য সবসময় http)
    scheme = 'http' # এই প্রক্সি শুধুমাত্র HTTP সমর্থন করে

    # গন্তব্য URL তৈরি
    # request.full_path পাথ এবং কোয়েরি স্ট্রিং দেয় (? সহ)
    destination_url = f"{scheme}://{host}{request.full_path}"

    print(f"[*] ফরওয়ার্ডিং অনুরোধ: {request.method} {destination_url}")

    try:
        # ডেস্টিনেশন সার্ভারে অনুরোধ পাঠানো
        # requests লাইব্রেরি ব্যবহার করে এটি করা সহজ
        resp = requests.request(
            method=request.method,
            url=destination_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'}, # মূল Host হেডার বাদ দিয়ে নতুন URL অনুযায়ী requests নিজেই Host সেট করবে
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False, # রিডাইরেক্ট প্রক্সির মাধ্যমে হ্যান্ডেল না করাই ভালো
            stream=True # বড় রেসপন্সের জন্য স্ট্রিম করা ভালো
        )

        # মূল ক্লায়েন্টের কাছে রেসপন্স ফেরত পাঠানো
        # হেডারগুলো কপি করা (কিছু হেডার বাদ দেওয়া যেতে পারে)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        # Flask রেসপন্স তৈরি
        response = Response(resp.content, resp.status_code, headers)
        return response

    except requests.exceptions.RequestException as e:
        print(f"[!] ডেস্টিনেশন সার্ভারে সংযোগ করতে সমস্যা: {e}")
        return f"Proxy error: Could not connect to destination server. Reason: {e}", 502 # 502 Bad Gateway

if __name__ == '__main__':
    # Render সাধারণত gunicorn ব্যবহার করে, তাই এই অংশটি লোকাল টেস্টিংয়ের জন্য
    # Render-এ সরাসরি এটি রান হবে না, নিচের Dockerfile CMD রান হবে
    app.run(host='0.0.0.0', port=8080, debug=False) # debug=True প্রোডাকশনে ব্যবহার করবেন না
