import socket
import threading
import sys

# কনফিগারেশন
LISTENING_HOST = '0.0.0.0'  # সব ইন্টারফেসে শুনবে
LISTENING_PORT = 8888      # এই পোর্টে প্রক্সি চলবে
MAX_CONNECTIONS = 5        # একবারে কতজন কানেক্ট করতে পারবে
BUFFER_SIZE = 4096         # ডেটা ট্রান্সফারের জন্য বাফার সাইজ

def handle_client(client_socket):
    """ক্লায়েন্টের অনুরোধ হ্যান্ডেল করে এবং ডেস্টিনেশন সার্ভারে পাঠায়"""
    try:
        # ক্লায়েন্টের কাছ থেকে প্রাথমিক অনুরোধ গ্রহণ
        request_data = client_socket.recv(BUFFER_SIZE)
        if not request_data:
            print("[-] ক্লায়েন্টের কাছ থেকে কোনো ডেটা আসেনি।")
            return

        # অনুরোধ থেকে প্রথম লাইন (যেমন GET http://example.com/ HTTP/1.1) পার্স করা
        first_line = request_data.split(b'\n')[0]
        url = first_line.split(b' ')[1]

        # হোস্ট এবং পোর্ট বের করা
        http_pos = url.find(b'://')
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]

        port_pos = temp.find(b':')
        webserver_pos = temp.find(b'/')
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80  # ডিফল্ট HTTP পোর্ট
            webserver = temp[:webserver_pos]
        else:
            port = int(temp[(port_pos + 1):][:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        print(f"[+] ডেস্টিনেশন সার্ভার: {webserver.decode()} পোর্ট: {port}")

        # ডেস্টিনেশন সার্ভারের সাথে সংযোগ স্থাপন
        proxy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_server_socket.connect((webserver, port))

        # ক্লায়েন্টের মূল অনুরোধটি ডেস্টিনেশন সার্ভারে পাঠানো
        proxy_server_socket.sendall(request_data)

        print(f"[+] ক্লায়েন্ট থেকে {webserver.decode()}:{port} এ ডেটা ফরওয়ার্ড করা হচ্ছে...")

        # ডেটা আদান-প্রদান (রিলে)
        while True:
            # ডেস্টিনেশন সার্ভার থেকে ডেটা পড়া
            reply = proxy_server_socket.recv(BUFFER_SIZE)
            if len(reply) > 0:
                # ক্লায়েন্টের কাছে ডেটা পাঠানো
                client_socket.send(reply)
                print(f"[<] {webserver.decode()}:{port} থেকে ক্লায়েন্টের কাছে ডেটা পাঠানো হচ্ছে ({len(reply)} বাইট)")
            else:
                # যদি কোনো ডেটা না আসে, ব্রেক
                break

        # সকেট বন্ধ করা
        proxy_server_socket.close()
        client_socket.close()
        print(f"[*] {webserver.decode()}:{port} এর সাথে সংযোগ বন্ধ করা হয়েছে।")

    except Exception as e:
        print(f"[!] ক্লায়েন্ট হ্যান্ডেলিং এরর: {e}")
        # কোনো সমস্যা হলে সকেট বন্ধ করে দেওয়া
        if 'client_socket' in locals() and client_socket:
             client_socket.close()
        if 'proxy_server_socket' in locals() and proxy_server_socket:
             proxy_server_socket.close()


def start_proxy_server():
    """প্রক্সি সার্ভার শুরু করে এবং ইনকামিং সংযোগের জন্য অপেক্ষা করে"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((LISTENING_HOST, LISTENING_PORT))
        server.listen(MAX_CONNECTIONS)
        print(f"[*] প্রক্সি সার্ভার {LISTENING_HOST}:{LISTENING_PORT} এ চলছে...")
    except Exception as e:
        print(f"[!] সার্ভার চালু করা যায়নি: {e}")
        sys.exit(1)

    while True:
        try:
            client_socket, addr = server.accept()
            print(f"\n[+] নতুন সংযোগ এসেছে: {addr[0]}:{addr[1]}")
            # প্রতিটি ক্লায়েন্টের জন্য একটি নতুন থ্রেড তৈরি করা
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
        except KeyboardInterrupt:
            print("\n[*] ব্যবহারকারী দ্বারা সার্ভার বন্ধ করা হচ্ছে...")
            server.close()
            sys.exit(0)
        except Exception as e:
            print(f"[!] সংযোগ গ্রহণ করার সময় ত্রুটি: {e}")

if __name__ == '__main__':
    start_proxy_server()
