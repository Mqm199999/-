
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import requests
import json
import os
from datetime import datetime
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)
app.secret_key = 'tiktok-downloader-2024-pro'

def get_user_language():
    try:
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if user_ip and user_ip != '127.0.0.1':
            response = requests.get(f'http://ipapi.co/{user_ip}/json/', timeout=5)
            country_code = response.json().get('country_code', 'US')
            arabic_countries = ['SA', 'EG', 'AE', 'JO', 'LB', 'SY', 'IQ', 'YE', 'KW', 'QA', 'BH', 'OM', 'MA', 'TN', 'DZ', 'LY', 'SD', 'PS']
            return 'ar' if country_code in arabic_countries else 'en'
    except Exception as e:
        pass
    return 'ar'

translations = {
    'ar': {
        'title': 'تحميل فيديوهات TikTok',
        'subtitle': 'حمل فيديوهاتك المفضلة بسهولة وسرعة',
        'placeholder': 'ضع رابط الفيديو هنا...',
        'download_btn': 'تحميل',
        'video_quality': 'جودة الفيديو',
        'audio_quality': 'جودة الصوت',
        'download_video': 'تحميل الفيديو',
        'download_audio': 'تحميل الصوت فقط',
        'processing': 'جاري المعالجة...',
        'error': 'حدث خطأ، يرجى المحاولة مرة أخرى',
        'invalid_url': 'رابط غير صحيح',
        'copyright': 'جميع الحقوق محفوظة - محمد قاسم',
        'features_title': 'مميزات الموقع',
        'feature_1_title': 'تحميل سريع',
        'feature_1_desc': 'تحميل فوري للفيديوهات بأعلى جودة',
        'feature_2_title': 'مجاني تماماً',
        'feature_2_desc': 'جميع الخدمات مجانية بدون قيود',
        'feature_3_title': 'آمن وموثوق',
        'feature_3_desc': 'حماية كاملة لبياناتك الشخصية',
        'how_to_title': 'كيفية الاستخدام',
        'step_1': 'انسخ رابط الفيديو من TikTok',
        'step_2': 'الصق الرابط في الحقل أعلاه',
        'step_3': 'اضغط على زر التحميل',
        'step_4': 'احفظ الفيديو على جهازك',
        'download_success': 'تم التحميل بدون علامة مائية!',
        'file_size': 'حجم الملف',
        'duration': 'المدة',
        'author': 'المؤلف',
        'welcome_title': 'مرحباً بك في عالم التحميل المجاني',
        'welcome_subtitle': 'حمل فيديوهات TikTok بجودة عالية وبدون علامة مائية'
    },
    'en': {
        'title': 'TikTok Video Downloader',
        'subtitle': 'Download your favorite videos easily and quickly',
        'placeholder': 'Paste video link here...',
        'download_btn': 'Download',
        'video_quality': 'Video Quality',
        'audio_quality': 'Audio Quality',
        'download_video': 'Download Video',
        'download_audio': 'Download Audio Only',
        'processing': 'Processing...',
        'error': 'An error occurred, please try again',
        'invalid_url': 'Invalid URL',
        'copyright': 'All Rights Reserved - Mohamed Qasem',
        'features_title': 'Website Features',
        'feature_1_title': 'Fast Download',
        'feature_1_desc': 'Instant video download with highest quality',
        'feature_2_title': 'Completely Free',
        'feature_2_desc': 'All services are free without limitations',
        'feature_3_title': 'Safe & Secure',
        'feature_3_desc': 'Complete protection for your personal data',
        'how_to_title': 'How to Use',
        'step_1': 'Copy video link from TikTok',
        'step_2': 'Paste the link in the field above',
        'step_3': 'Click the download button',
        'step_4': 'Save the video to your device',
        'download_success': 'Downloaded without watermark!',
        'file_size': 'File Size',
        'duration': 'Duration',
        'author': 'Author',
        'welcome_title': 'Welcome to Free Download World',
        'welcome_subtitle': 'Download TikTok videos in high quality without watermark'
    }
}

def clean_tiktok_url(url):
    pattern = r'https?://[^/]*tiktok\.com/[^?\s]*'
    match = re.search(pattern, url)
    if match:
        return match.group(0)
    return url

def download_tiktok_video(url):
    clean_url = clean_tiktok_url(url)
    api_url = "https://downloader.bot/api/tiktok/info"

    payload = {"url": clean_url}

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua': "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://downloader.bot",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://downloader.bot/ar",
        'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        'priority': "u=1, i",
        'Cookie': "lang=ar; _ga_233R9NY1HK=GS2.1.s1759102487$o1$g0$t1759102487$j60$l0$h0; _ga=GA1.1.1944387372.1759102487"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()

            if data.get('status') and data.get('data'):
                vd = data['data']

                if vd.get('mp4') and vd.get('mp3'):
                    return {
                        'nick': vd.get('nick', 'مستخدم TikTok'),
                        'video_info': vd.get('video_info', 'فيديو TikTok رائع'),
                        'mp4': vd.get('mp4', ''),
                        'mp3': vd.get('mp3', ''),
                        'video_date': vd.get('video_date', int(datetime.now().timestamp())),
                        'duration': 'غير محدد',
                        'file_size': 0
                    }
                else:
                    return None
            else:
                return None
        else:
            return None

    except Exception as e:
        return None

def validate_tiktok_url(url):
    tiktok_patterns = [
        r'https?://.*tiktok\.com',
        r'https?://vt\.tiktok\.com',
        r'https?://vm\.tiktok\.com',
        r'https?://m\.tiktok\.com'
    ]

    url = url.strip().lower()
    for pattern in tiktok_patterns:
        if re.search(pattern, url):
            return True
    return False

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "غير محدد"
    size_names = ["بايت", "كيلوبايت", "ميجابايت", "جيجابايت"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}" dir="{{ 'rtl' if lang == 'ar' else 'ltr' }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <meta name="description" content="{{ t.subtitle }}">
    <meta name="keywords" content="TikTok, Download, Video, Audio, Free">
    <link rel="icon" type="image/x-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='%23fe2c55' d='M19.589 6.686a4.793 4.793 0 0 1-3.77-4.245V2h-3.445v13.672a2.896 2.896 0 0 1-5.201 1.743l-.002-.001.002.001a2.895 2.895 0 0 1 3.183-4.51v-3.5a6.329 6.329 0 0 0-5.394 10.692 6.33 6.33 0 0 0 10.857-4.424V8.687a8.182 8.182 0 0 0 4.773 1.526V6.79a4.831 4.831 0 0 1-1.003-.104z'/></svg>">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-color: #fe2c55;
            --secondary-color: #25f4ee;
            --dark-color: #161823;
            --light-color: #ffffff;
            --gray-color: #f8f8f8;
            --text-dark: #333333;
            --text-light: #666666;
            --gradient: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            --gradient-2: linear-gradient(45deg, #ff0050, #ff4081, #9c27b0);
            --shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            --shadow-hover: 0 20px 40px rgba(0, 0, 0, 0.15);
            --border-radius: 20px;
            --transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            --glass-bg: rgba(255, 255, 255, 0.25);
            --glass-border: rgba(255, 255, 255, 0.18);
        }

        body {
            font-family: 'Cairo', 'Poppins', sans-serif;
            line-height: 1.6;
            color: var(--text-dark);
            overflow-x: hidden;
            scroll-behavior: smooth;
        }

        [dir="rtl"] {
            font-family: 'Cairo', sans-serif;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 30px;
        }

        .preloader {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            opacity: 1;
            visibility: visible;
            transition: all 0.6s ease-in-out;
        }

        .preloader.fade-out {
            opacity: 0;
            visibility: hidden;
        }

        .preloader-content {
            text-align: center;
            color: white;
        }

        .tiktok-spinner {
            font-size: 4rem;
            margin-bottom: 30px;
            animation: tiktokSpin 2s infinite linear;
        }

        .preloader-content h2 {
            font-size: 2.5rem;
            margin-bottom: 15px;
            animation: fadeInUp 1s ease-out;
        }

        .preloader-content p {
            font-size: 1.2rem;
            opacity: 0.9;
            animation: fadeInUp 1s ease-out 0.3s both;
        }

        @keyframes tiktokSpin {
            0% { transform: rotate(0deg) scale(1); }
            25% { transform: rotate(90deg) scale(1.1); }
            50% { transform: rotate(180deg) scale(1); }
            75% { transform: rotate(270deg) scale(1.1); }
            100% { transform: rotate(360deg) scale(1); }
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 1.5rem 0;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            transition: var(--transition);
        }

        .header.scrolled {
            padding: 1rem 0;
            background: rgba(255, 255, 255, 0.98);
            box-shadow: var(--shadow);
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary-color);
            text-decoration: none;
        }

        .logo i {
            font-size: 2.5rem;
            animation: pulse 2s infinite;
        }

        .pulse-animation {
            animation: pulseGlow 2s ease-in-out infinite;
        }

        @keyframes pulseGlow {
            0%, 100% { 
                transform: scale(1); 
                filter: drop-shadow(0 0 10px var(--primary-color));
            }
            50% { 
                transform: scale(1.1); 
                filter: drop-shadow(0 0 20px var(--primary-color));
            }
        }

        .language-switcher {
            display: flex;
            gap: 10px;
        }

        .language-switcher a {
            padding: 12px 20px;
            text-decoration: none;
            color: var(--text-light);
            border-radius: 30px;
            transition: var(--transition);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 0, 0, 0.05);
        }

        .language-switcher a.active,
        .language-switcher a:hover {
            background: var(--gradient);
            color: white;
            transform: translateY(-3px);
            box-shadow: var(--shadow);
        }

        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            background: var(--gradient);
            position: relative;
            overflow: hidden;
            padding-top: 120px;
        }

        .hero-content {
            text-align: center;
            color: white;
            z-index: 2;
            position: relative;
            width: 100%;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 20px;
            border-radius: 50px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            animation: fadeInUp 1s ease-out;
        }

        .hero-title {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            animation: fadeInUp 1s ease-out 0.2s both;
            background: linear-gradient(45deg, #ffffff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }

        .hero-subtitle {
            font-size: 1.4rem;
            margin-bottom: 3rem;
            opacity: 0.95;
            animation: fadeInUp 1s ease-out 0.4s both;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .stats-section {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            padding: 40px 30px;
            margin-bottom: 50px;
            animation: fadeInUp 1s ease-out 0.5s both;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 40px;
            align-items: center;
        }

        .stat-card {
            text-align: center;
            position: relative;
            padding: 20px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .stat-card:hover {
            transform: translateY(-10px) scale(1.05);
            background: rgba(255, 255, 255, 0.2);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
        }

        .stat-number {
            font-size: 3.5rem;
            font-weight: 900;
            display: block;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #ffffff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            line-height: 1;
        }

        .stat-label {
            font-size: 1.1rem;
            font-weight: 600;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .stat-icon {
            position: absolute;
            top: -15px;
            right: 15px;
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, #25f4ee, #ffffff);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--primary-color);
            font-size: 1.2rem;
            box-shadow: 0 5px 15px rgba(37, 244, 238, 0.3);
        }

        .download-form {
            max-width: 700px;
            margin: 0 auto 40px;
            animation: fadeInUp 1s ease-out 0.8s both;
        }

        .input-group {
            display: flex;
            gap: 15px;
            background: var(--glass-bg);
            padding: 15px;
            border-radius: var(--border-radius);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow);
        }

        .input-wrapper {
            flex: 1;
            position: relative;
        }

        .input-icon {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-light);
            font-size: 1.1rem;
            z-index: 2;
        }

        [dir="rtl"] .input-icon {
            right: 20px;
            left: auto;
        }

        .url-input {
            width: 100%;
            padding: 18px 20px 18px 50px;
            border: 2px solid transparent;
            border-radius: 15px;
            font-size: 1.1rem;
            background: rgba(255, 255, 255, 0.95);
            color: var(--text-dark);
            outline: none;
            transition: var(--transition);
            position: relative;
        }

        [dir="rtl"] .url-input {
            padding: 18px 50px 18px 20px;
        }

        .url-input:focus {
            background: white;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            border-color: white;
        }

        .input-border {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 0;
            height: 3px;
            background: var(--gradient);
            transition: var(--transition);
            border-radius: 2px;
        }

        .url-input:focus + .input-border {
            width: 100%;
        }

        .download-btn {
            padding: 18px 35px;
            background: var(--dark-color);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 12px;
            white-space: nowrap;
            position: relative;
            overflow: hidden;
            min-width: 150px;
            justify-content: center;
        }

        .download-btn:hover {
            background: #000;
            transform: translateY(-3px);
            box-shadow: var(--shadow-hover);
        }

        .download-btn:active {
            transform: translateY(-1px);
        }

        .btn-text {
            display: flex;
            align-items: center;
            gap: 10px;
            transition: var(--transition);
        }

        .btn-loader {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            opacity: 0;
            transition: var(--transition);
        }

        .download-btn.loading .btn-text {
            opacity: 0;
        }

        .download-btn.loading .btn-loader {
            opacity: 1;
        }

        .spinner-small {
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        .security-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 0, 0, 0.2);
            padding: 8px 16px;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 500;
            animation: fadeInUp 1s ease-out 1s both;
        }

        .notification {
            position: fixed;
            top: 30px;
            right: 30px;
            background: white;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-hover);
            padding: 20px;
            min-width: 350px;
            z-index: 5000;
            transform: translateX(400px);
            transition: var(--transition);
        }

        [dir="rtl"] .notification {
            left: 30px;
            right: auto;
            transform: translateX(-400px);
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification-content {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .notification-icon {
            font-size: 2rem;
            color: #28a745;
        }

        .notification-text h4 {
            margin-bottom: 5px;
            color: var(--text-dark);
        }

        .notification-text p {
            color: var(--text-light);
            font-size: 0.9rem;
        }

        .notification-progress {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 4px;
            background: #28a745;
            border-radius: 0 0 var(--border-radius) var(--border-radius);
            animation: progressBar 4s linear;
        }

        @keyframes progressBar {
            from { width: 100%; }
            to { width: 0%; }
        }

        .success-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(40, 167, 69, 0.3);
            z-index: 10000;
            transform: translateX(400px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 500;
            min-width: 250px;
        }

        .success-notification.show {
            transform: translateX(0);
            opacity: 1;
        }

        .success-notification .notification-content {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .success-notification i {
            font-size: 1.2rem;
            animation: checkAnimation 0.5s ease-in-out;
        }

        @keyframes checkAnimation {
            0% { transform: scale(0); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }

        [dir="rtl"] .success-notification {
            right: auto;
            left: 20px;
            transform: translateX(-400px);
        }

        [dir="rtl"] .success-notification.show {
            transform: translateX(0);
        }

        .hero-bg {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            overflow: hidden;
        }

        .floating-icons {
            position: absolute;
            width: 100%;
            height: 100%;
        }

        .floating-icons i {
            position: absolute;
            color: rgba(255, 255, 255, 0.1);
            font-size: 2rem;
            animation: float 8s ease-in-out infinite;
        }

        .floating-icons i:nth-child(1) { top: 15%; left: 10%; animation-delay: 0s; font-size: 3rem; }
        .floating-icons i:nth-child(2) { top: 25%; right: 15%; animation-delay: 1s; }
        .floating-icons i:nth-child(3) { bottom: 35%; left: 20%; animation-delay: 2s; font-size: 2.5rem; }
        .floating-icons i:nth-child(4) { top: 45%; right: 30%; animation-delay: 3s; }
        .floating-icons i:nth-child(5) { bottom: 25%; right: 10%; animation-delay: 4s; font-size: 3.5rem; }
        .floating-icons i:nth-child(6) { top: 60%; left: 15%; animation-delay: 5s; }
        .floating-icons i:nth-child(7) { bottom: 50%; right: 25%; animation-delay: 6s; font-size: 2.8rem; }
        .floating-icons i:nth-child(8) { top: 30%; left: 40%; animation-delay: 7s; }

        .gradient-orbs {
            position: absolute;
            width: 100%;
            height: 100%;
        }

        .orb {
            position: absolute;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.1));
            animation: orbFloat 12s ease-in-out infinite;
        }

        .orb-1 {
            width: 200px;
            height: 200px;
            top: 20%;
            left: 10%;
            animation-delay: 0s;
        }

        .orb-2 {
            width: 150px;
            height: 150px;
            bottom: 20%;
            right: 20%;
            animation-delay: 4s;
        }

        .orb-3 {
            width: 100px;
            height: 100px;
            top: 60%;
            left: 70%;
            animation-delay: 8s;
        }

        @keyframes orbFloat {
            0%, 100% { transform: translateY(0px) scale(1); }
            50% { transform: translateY(-30px) scale(1.1); }
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(10px);
        }

        .modal-content {
            background-color: white;
            margin: 3% auto;
            padding: 40px;
            border-radius: var(--border-radius);
            width: 90%;
            max-width: 600px;
            position: relative;
            animation: modalSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            max-height: 90vh;
            overflow-y: auto;
        }

        .loading-modal-content {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .result-modal-content {
            padding: 20px;
        }

        .close {
            color: #999;
            position: absolute;
            right: 20px;
            top: 15px;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            transition: var(--transition);
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .close:hover {
            background: rgba(0, 0, 0, 0.1);
            color: var(--primary-color);
            transform: scale(1.1);
        }

        .loading-spinner {
            padding: 30px;
        }

        .advanced-spinner {
            position: relative;
            width: 120px;
            height: 120px;
            margin: 0 auto 30px;
        }

        .spinner-ring {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 3px solid transparent;
            animation: spinRing 2s linear infinite;
        }

        .spinner-ring:nth-child(1) {
            border-top-color: #fff;
            animation-delay: 0s;
        }

        .spinner-ring:nth-child(2) {
            border-right-color: rgba(255, 255, 255, 0.7);
            animation-delay: 0.3s;
            animation-direction: reverse;
        }

        .spinner-ring:nth-child(3) {
            border-bottom-color: rgba(255, 255, 255, 0.4);
            animation-delay: 0.6s;
        }

        .spinner-icon {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 2.5rem;
            animation: pulse 1.5s ease-in-out infinite;
        }

        .loading-spinner h3 {
            font-size: 1.5rem;
            margin-bottom: 10px;
        }

        .loading-steps {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 30px;
        }

        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            opacity: 0.5;
            transition: var(--transition);
        }

        .step.active {
            opacity: 1;
            transform: scale(1.1);
        }

        .step i {
            font-size: 1.5rem;
            margin-bottom: 5px;
        }

        @keyframes spinRing {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .result-card {
            background: white;
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--shadow);
            margin-bottom: 20px;
        }

        .video-thumbnail {
            width: 100%;
            height: 250px;
            object-fit: cover;
            transition: var(--transition);
        }

        .video-thumbnail:hover {
            transform: scale(1.05);
        }

        .video-info {
            padding: 30px;
        }

        .video-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 15px;
            color: var(--text-dark);
            line-height: 1.5;
        }

        .video-author {
            color: var(--text-light);
            margin-bottom: 25px;
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .video-author::before {
            content: '👤';
            font-size: 1.2rem;
        }

        .download-options {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .download-option {
            flex: 1;
            min-width: 140px;
            padding: 15px 25px;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: var(--transition);
            text-decoration: none;
            text-align: center;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            font-size: 1rem;
        }

        .download-video {
            background: var(--gradient);
            color: white;
        }

        .download-audio {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }

        .download-option:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: var(--shadow-hover);
        }

        .features {
            padding: 100px 0;
            background: var(--gray-color);
            position: relative;
        }

        .section-header {
            text-align: center;
            margin-bottom: 60px;
        }

        .section-header h2 {
            font-size: 3rem;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 20px;
        }

        .section-header p {
            font-size: 1.2rem;
            color: var(--text-light);
            max-width: 600px;
            margin: 0 auto;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 40px;
        }

        .feature-card {
            background: white;
            padding: 50px 40px;
            border-radius: var(--border-radius);
            text-align: center;
            transition: var(--transition);
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: var(--gradient);
            transform: scaleX(0);
            transition: var(--transition);
        }

        .feature-card:hover::before {
            transform: scaleX(1);
        }

        .feature-card:hover {
            transform: translateY(-15px);
            box-shadow: var(--shadow-hover);
        }

        .feature-icon {
            position: relative;
            width: 100px;
            height: 100px;
            background: var(--gradient);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 30px;
            color: white;
            font-size: 2.5rem;
        }

        .icon-glow {
            position: absolute;
            top: -5px;
            left: -5px;
            right: -5px;
            bottom: -5px;
            background: var(--gradient);
            border-radius: 50%;
            opacity: 0.3;
            animation: pulse 2s infinite;
        }

        .feature-card h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: var(--text-dark);
        }

        .feature-card p {
            color: var(--text-light);
            line-height: 1.7;
            font-size: 1.1rem;
        }

        .how-to-use {
            padding: 100px 0;
            background: white;
        }

        .steps-container {
            display: flex;
            justify-content: space-between;
            gap: 40px;
            margin-top: 60px;
        }

        .step-item {
            flex: 1;
            text-align: center;
            position: relative;
        }

        .step-item::before {
            content: attr(data-step);
            position: absolute;
            top: -20px;
            right: -20px;
            width: 40px;
            height: 40px;
            background: var(--gradient);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.1rem;
        }

        .step-icon {
            width: 80px;
            height: 80px;
            background: var(--gray-color);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            color: var(--primary-color);
            font-size: 2rem;
            transition: var(--transition);
        }

        .step-item:hover .step-icon {
            background: var(--gradient);
            color: white;
            transform: scale(1.1);
        }

        .step-content h4 {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 10px;
            color: var(--text-dark);
        }

        .step-content p {
            color: var(--text-light);
            font-size: 1rem;
        }

        .footer {
            background: var(--dark-color);
            color: white;
            padding: 60px 0 20px;
        }

        .footer-main {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 50px;
            margin-bottom: 40px;
            padding-bottom: 40px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .footer-brand .logo {
            color: white;
            margin-bottom: 20px;
        }

        .footer-brand p {
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.6;
            font-size: 1.1rem;
        }

        .footer-section h4 {
            font-size: 1.2rem;
            margin-bottom: 20px;
            color: white;
        }

        .footer-section ul {
            list-style: none;
        }

        .footer-section ul li {
            margin-bottom: 10px;
        }

        .footer-section ul li a {
            color: rgba(255, 255, 255, 0.7);
            text-decoration: none;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .footer-section ul li a:hover {
            color: var(--primary-color);
            transform: translateX(5px);
        }

        .social-links {
            display: flex;
            gap: 15px;
        }

        .social-links a {
            width: 45px;
            height: 45px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.2rem;
            transition: var(--transition);
        }

        .social-links a:hover {
            background: var(--primary-color);
            transform: translateY(-3px);
        }

        .footer-bottom {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 20px;
        }

        .footer-badges {
            display: flex;
            gap: 20px;
        }

        .badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.8);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slideIn {
            from { transform: translateY(-100%); }
            to { transform: translateY(0); }
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }

        @keyframes bounce {
            0%, 20%, 53%, 80%, 100% { transform: translateY(0); }
            40%, 43% { transform: translateY(-15px); }
            70% { transform: translateY(-7px); }
            90% { transform: translateY(-3px); }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes modalSlideIn {
            from { opacity: 0; transform: scale(0.8) translateY(-50px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 1200px) {
            .container {
                padding: 0 20px;
            }
        }

        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.8rem;
            }

            .input-group {
                flex-direction: column;
                gap: 15px;
            }

            .download-btn {
                justify-content: center;
                min-width: auto;
            }

            .stats-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            .features-grid {
                grid-template-columns: 1fr;
                gap: 30px;
            }

            .steps-container {
                flex-direction: column;
                gap: 40px;
            }

            .footer-main {
                grid-template-columns: 1fr;
                gap: 30px;
            }

            .footer-bottom {
                flex-direction: column;
                gap: 20px;
            }

            .modal-content {
                margin: 10% auto;
                width: 95%;
                padding: 25px;
            }

            .section-header h2 {
                font-size: 2.2rem;
            }

            .notification {
                min-width: 300px;
                right: 15px;
                top: 15px;
            }

            [dir="rtl"] .notification {
                left: 15px;
            }
        }

        @media (max-width: 480px) {
            .hero-title {
                font-size: 2.2rem;
            }

            .hero-subtitle {
                font-size: 1.1rem;
            }

            .container {
                padding: 0 15px;
            }

            .header-content {
                flex-direction: column;
                gap: 15px;
            }

            .preloader-content h2 {
                font-size: 1.8rem;
            }

            .download-options {
                flex-direction: column;
            }

            .notification {
                min-width: 280px;
                right: 10px;
                top: 10px;
            }

            [dir="rtl"] .notification {
                left: 10px;
            }

            .stat-number {
                font-size: 2.5rem;
            }
        }

        [dir="rtl"] .header-content,
        [dir="rtl"] .input-group,
        [dir="rtl"] .footer-content,
        [dir="rtl"] .notification-content {
            direction: rtl;
        }

        [dir="rtl"] .close {
            left: 20px;
            right: auto;
        }

        [dir="rtl"] .footer-section ul li a:hover {
            transform: translateX(-5px);
        }

        .feature-card,
        .step-item,
        .modal {
            will-change: transform;
        }

        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>
</head>
<body>
    <div id="preloader" class="preloader">
        <div class="preloader-content">
            <div class="tiktok-spinner">
                <i class="fab fa-tiktok"></i>
            </div>
            <h2>{{ t.welcome_title }}</h2>
            <p>{{ t.welcome_subtitle }}</p>
        </div>
    </div>

    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fab fa-tiktok pulse-animation"></i>
                    <span>TikDownloader Pro</span>
                </div>
                <div class="language-switcher">
                    <a href="/set_language/ar" class="{{ 'active' if lang == 'ar' else '' }}">
                        <i class="fas fa-globe"></i> العربية
                    </a>
                    <a href="/set_language/en" class="{{ 'active' if lang == 'en' else '' }}">
                        <i class="fas fa-globe"></i> English
                    </a>
                </div>
            </div>
        </div>
    </header>

    <section class="hero">
        <div class="container">
            <div class="hero-content">
                <div class="hero-badge">
                    <i class="fas fa-crown"></i>
                    <span>{{ 'المميز والمجاني' if lang == 'ar' else 'Premium & Free' }}</span>
                </div>
                
                <h1 class="hero-title">{{ t.title }}</h1>
                <p class="hero-subtitle">{{ t.subtitle }}</p>
                
                <div class="download-form">
                    <div class="input-group">
                        <div class="input-wrapper">
                            <i class="fas fa-link input-icon"></i>
                            <input type="url" id="videoUrl" placeholder="{{ t.placeholder }}" class="url-input">
                            <div class="input-border"></div>
                        </div>
                        <button onclick="downloadVideo()" class="download-btn">
                            <span class="btn-text">
                                <i class="fas fa-download"></i>
                                {{ t.download_btn }}
                            </span>
                            <div class="btn-loader">
                                <div class="spinner-small"></div>
                            </div>
                        </button>
                    </div>
                </div>
                
                <div class="stats-section">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-download"></i>
                            </div>
                            <div class="stat-number" data-count="1000000">0</div>
                            <div class="stat-label">{{ 'تحميل' if lang == 'ar' else 'Downloads' }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-users"></i>
                            </div>
                            <div class="stat-number" data-count="50000">0</div>
                            <div class="stat-label">{{ 'مستخدم' if lang == 'ar' else 'Users' }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fas fa-star"></i>
                            </div>
                            <div class="stat-number" data-count="100">0</div>
                            <div class="stat-label">%</div>
                        </div>
                    </div>
                </div>

                <div class="security-badge">
                    <i class="fas fa-shield-alt"></i>
                    <span>{{ '100% آمن وخالي من الفيروسات' if lang == 'ar' else '100% Safe & Virus Free' }}</span>
                </div>
            </div>
        </div>
        
        <div class="hero-bg">
            <div class="floating-icons">
                <i class="fab fa-tiktok"></i>
                <i class="fas fa-music"></i>
                <i class="fas fa-video"></i>
                <i class="fas fa-heart"></i>
                <i class="fas fa-star"></i>
                <i class="fas fa-download"></i>
                <i class="fas fa-mobile-alt"></i>
                <i class="fas fa-play"></i>
            </div>
            <div class="gradient-orbs">
                <div class="orb orb-1"></div>
                <div class="orb orb-2"></div>
                <div class="orb orb-3"></div>
            </div>
        </div>
    </section>

    <div id="successNotification" class="notification success-notification">
        <div class="notification-content">
            <div class="notification-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <div class="notification-text">
                <h4>{{ t.download_success }}</h4>
                <p>{{ 'جودة عالية بدون علامة مائية' if lang == 'ar' else 'High quality without watermark' }}</p>
            </div>
        </div>
        <div class="notification-progress"></div>
    </div>

    <div id="loadingModal" class="modal">
        <div class="modal-content loading-modal-content">
            <div class="loading-spinner">
                <div class="advanced-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <i class="fab fa-tiktok spinner-icon"></i>
                </div>
                <h3>{{ t.processing }}</h3>
                <p>{{ 'جاري تحليل الفيديو وإعداد الروابط...' if lang == 'ar' else 'Analyzing video and preparing links...' }}</p>
                <div class="loading-steps">
                    <div class="step active">
                        <i class="fas fa-link"></i>
                        <span>{{ 'تحليل الرابط' if lang == 'ar' else 'Analyzing URL' }}</span>
                    </div>
                    <div class="step">
                        <i class="fas fa-download"></i>
                        <span>{{ 'تحضير الملفات' if lang == 'ar' else 'Preparing Files' }}</span>
                    </div>
                    <div class="step">
                        <i class="fas fa-check"></i>
                        <span>{{ 'جاهز للتحميل' if lang == 'ar' else 'Ready to Download' }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="resultModal" class="modal">
        <div class="modal-content result-modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="resultContent"></div>
        </div>
    </div>

    <section class="features">
        <div class="container">
            <div class="section-header">
                <h2>{{ 'لماذا نحن الأفضل؟' if lang == 'ar' else 'Why Choose Us?' }}</h2>
                <p>{{ 'اكتشف المميزات الرائعة التي تجعلنا الخيار الأول' if lang == 'ar' else 'Discover amazing features that make us the top choice' }}</p>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-rocket"></i>
                        <div class="icon-glow"></div>
                    </div>
                    <h3>{{ 'سرعة فائقة' if lang == 'ar' else 'Lightning Fast' }}</h3>
                    <p>{{ 'تحميل فوري للفيديوهات بأعلى جودة ممكنة' if lang == 'ar' else 'Instant video downloads with highest possible quality' }}</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-gem"></i>
                        <div class="icon-glow"></div>
                    </div>
                    <h3>{{ 'جودة عالية' if lang == 'ar' else 'Premium Quality' }}</h3>
                    <p>{{ 'احتفظ بجودة الفيديو الأصلية بدون ضغط' if lang == 'ar' else 'Preserve original video quality without compression' }}</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-shield-alt"></i>
                        <div class="icon-glow"></div>
                    </div>
                    <h3>{{ 'آمن 100%' if lang == 'ar' else '100% Secure' }}</h3>
                    <p>{{ 'حماية كاملة لبياناتك الشخصية وخصوصيتك' if lang == 'ar' else 'Complete protection for your personal data and privacy' }}</p>
                </div>
            </div>
        </div>
    </section>

    <section class="how-to-use">
        <div class="container">
            <div class="section-header">
                <h2>{{ t.how_to_title }}</h2>
                <p>{{ 'خطوات بسيطة للحصول على فيديوهاتك المفضلة' if lang == 'ar' else 'Simple steps to get your favorite videos' }}</p>
            </div>
            
            <div class="steps-container">
                <div class="step-item" data-step="1">
                    <div class="step-icon">
                        <i class="fas fa-copy"></i>
                    </div>
                    <div class="step-content">
                        <h4>{{ t.step_1 }}</h4>
                        <p>{{ 'من التطبيق أو المتصفح' if lang == 'ar' else 'From app or browser' }}</p>
                    </div>
                </div>
                
                <div class="step-item" data-step="2">
                    <div class="step-icon">
                        <i class="fas fa-paste"></i>
                    </div>
                    <div class="step-content">
                        <h4>{{ t.step_2 }}</h4>
                        <p>{{ 'سيتم التعرف على الرابط تلقائياً' if lang == 'ar' else 'URL will be recognized automatically' }}</p>
                    </div>
                </div>
                
                <div class="step-item" data-step="3">
                    <div class="step-icon">
                        <i class="fas fa-download"></i>
                    </div>
                    <div class="step-content">
                        <h4>{{ t.step_3 }}</h4>
                        <p>{{ 'واحصل على النتيجة فوراً' if lang == 'ar' else 'And get results instantly' }}</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-main">
                    <div class="footer-brand">
                        <div class="logo">
                            <i class="fab fa-tiktok"></i>
                            <span>TikDownloader Pro</span>
                        </div>
                        <p>{{ 'أفضل موقع لتحميل فيديوهات TikTok بجودة عالية ومجاناً' if lang == 'ar' else 'The best site for downloading TikTok videos in high quality for free' }}</p>
                    </div>
                    
                    <div class="footer-links">
                        <div class="footer-section">
                            <h4>{{ 'روابط سريعة' if lang == 'ar' else 'Quick Links' }}</h4>
                            <ul>
                                <li><a href="#"><i class="fas fa-home"></i> {{ 'الرئيسية' if lang == 'ar' else 'Home' }}</a></li>
                                <li><a href="#"><i class="fas fa-info-circle"></i> {{ 'حولنا' if lang == 'ar' else 'About' }}</a></li>
                                <li><a href="#"><i class="fas fa-envelope"></i> {{ 'اتصل بنا' if lang == 'ar' else 'Contact' }}</a></li>
                            </ul>
                        </div>
                        
                        <div class="footer-section">
                            <h4>{{ 'تابعنا' if lang == 'ar' else 'Follow Us' }}</h4>
                            <div class="social-links">
                                <a href="https://t.me/ppx_s"><i class="fab fa-telegram"></i></a>
                                <a href="#"><i class="fab fa-twitter"></i></a>
                                <a href="#"><i class="fab fa-instagram"></i></a>
                                <a href="#"><i class="fab fa-facebook"></i></a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="footer-bottom">
                    <p>{{ t.copyright }}</p>
                    <div class="footer-badges">
                        <div class="badge">
                            <i class="fas fa-shield-alt"></i>
                            <span>{{ 'آمن' if lang == 'ar' else 'Secure' }}</span>
                        </div>
                        <div class="badge">
                            <i class="fas fa-zap"></i>
                            <span>{{ 'سريع' if lang == 'ar' else 'Fast' }}</span>
                        </div>
                        <div class="badge">
                            <i class="fas fa-heart"></i>
                            <span>{{ 'مجاني' if lang == 'ar' else 'Free' }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </footer>

    <script>
        const loadingModal = document.getElementById('loadingModal');
        const resultModal = document.getElementById('resultModal');
        const resultContent = document.getElementById('resultContent');
        const videoUrlInput = document.getElementById('videoUrl');
        const downloadBtn = document.querySelector('.download-btn');
        const preloader = document.getElementById('preloader');
        const successNotification = document.getElementById('successNotification');

        let currentLanguage = '{{ lang }}';
        let loadingSteps = [];
        let currentStep = 0;

        window.addEventListener('load', function() {
            setTimeout(() => {
                if (preloader) {
                    preloader.classList.add('fade-out');
                    setTimeout(() => {
                        preloader.style.display = 'none';
                    }, 600);
                }

                animateCounters();
                handleHeaderScroll();
            }, 1000);
        });

        function animateCounters() {
            const counters = document.querySelectorAll('.stat-number');

            counters.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-count'));
                const duration = 2000;
                const step = target / (duration / 16);
                let current = 0;

                const timer = setInterval(() => {
                    current += step;
                    if (current >= target) {
                        counter.textContent = target.toLocaleString();
                        clearInterval(timer);
                    } else {
                        counter.textContent = Math.floor(current).toLocaleString();
                    }
                }, 16);
            });
        }

        function handleHeaderScroll() {
            const header = document.querySelector('.header');

            window.addEventListener('scroll', () => {
                if (window.scrollY > 100) {
                    header.classList.add('scrolled');
                } else {
                    header.classList.remove('scrolled');
                }
            });
        }

        async function downloadVideo() {
            const url = videoUrlInput.value.trim();

            if (!url) {
                showError(getTranslation('error_no_url'));
                return;
            }

            if (!isValidTikTokUrl(url)) {
                showError(getTranslation('invalid_url'));
                return;
            }

            downloadBtn.classList.add('loading');

            showLoading();
            startLoadingSteps();

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                downloadBtn.classList.remove('loading');
                hideLoading();

                if (data.success) {
                    showResult(data.data);
                    showSuccessNotification();
                } else {
                    showError(data.error || getTranslation('download_error'));
                }
            } catch (error) {
                downloadBtn.classList.remove('loading');
                hideLoading();
                showError(getTranslation('connection_error'));
                console.error('Error:', error);
            }
        }

        function startLoadingSteps() {
            loadingSteps = document.querySelectorAll('.loading-steps .step');
            currentStep = 0;

            loadingSteps.forEach(step => step.classList.remove('active'));

            const stepInterval = setInterval(() => {
                if (currentStep < loadingSteps.length) {
                    loadingSteps[currentStep].classList.add('active');
                    currentStep++;
                } else {
                    clearInterval(stepInterval);
                }
            }, 1500);
        }

        function isValidTikTokUrl(url) {
            const tiktokPatterns = [
                /tiktok\.com/,
                /vt\.tiktok\.com/,
                /vm\.tiktok\.com/,
                /m\.tiktok\.com/
            ];

            return tiktokPatterns.some(pattern => pattern.test(url.toLowerCase()));
        }

        function showLoading() {
            loadingModal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }

        function hideLoading() {
            loadingModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        function showSuccessNotification() {
            successNotification.classList.add('show');

            setTimeout(() => {
                successNotification.classList.remove('show');
            }, 4000);
        }

        function showResult(data) {
            const isRTL = currentLanguage === 'ar';

            const html = `
                <div class="result-card">
                    <div class="video-info">
                        <div class="video-title">${data.video_info || (isRTL ? 'فيديو TikTok' : 'TikTok Video')}</div>
                        <div class="video-author">@${data.nick || (isRTL ? 'مستخدم' : 'User')}</div>

                        <div class="video-details" style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px;">
                            <div style="display: flex; gap: 20px; font-size: 0.9rem; color: #666;">
                                ${data.duration ? `<span><i class="fas fa-clock"></i> ${data.duration}</span>` : ''}
                                ${data.file_size ? `<span><i class="fas fa-file"></i> ${data.file_size}</span>` : ''}
                            </div>
                        </div>

                        <div class="download-options">
                            <a href="${data.mp4}" target="_blank" class="download-option download-video" onclick="trackDownload('video')">
                                <i class="fas fa-video"></i>
                                ${isRTL ? 'تحميل الفيديو' : 'Download Video'}
                            </a>
                            <a href="${data.mp3}" target="_blank" class="download-option download-audio" onclick="trackDownload('audio')">
                                <i class="fas fa-music"></i>
                                ${isRTL ? 'تحميل الصوت' : 'Download Audio'}
                            </a>
                        </div>

                        <div style="margin-top: 20px; text-align: center;">
                            <small style="color: #28a745; font-weight: 600;">
                                <i class="fas fa-check-circle"></i>
                                ${isRTL ? 'بدون علامة مائية - جودة عالية' : 'No Watermark - High Quality'}
                            </small>
                        </div>
                    </div>
                </div>
            `;

            resultContent.innerHTML = html;
            resultModal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }

        function trackDownload(type) {
            showSuccessNotification();
        }

        function showError(message) {
            const isRTL = currentLanguage === 'ar';

            const html = `
                <div class="error-message" style="text-align: center; padding: 40px;">
                    <div style="font-size: 4rem; color: #e74c3c; margin-bottom: 20px;">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h3 style="color: #e74c3c; margin-bottom: 15px; font-size: 1.5rem;">
                        ${isRTL ? 'حدث خطأ' : 'Error Occurred'}
                    </h3>
                    <p style="color: #666; font-size: 1.1rem; line-height: 1.6; max-width: 400px; margin: 0 auto;">
                        ${message}
                    </p>
                    <button onclick="closeModal()" style="margin-top: 25px; padding: 12px 30px; background: var(--primary-color); color: white; border: none; border-radius: 25px; font-weight: 600; cursor: pointer; font-size: 1rem;">
                        ${isRTL ? 'حسناً' : 'OK'}
                    </button>
                </div>
            `;

            resultContent.innerHTML = html;
            resultModal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }

        function closeModal() {
            resultModal.style.display = 'none';
            loadingModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        function getTranslation(key) {
            const translations = {
                'ar': {
                    'error_no_url': 'يرجى إدخال رابط الفيديو',
                    'invalid_url': 'رابط TikTok غير صحيح',
                    'download_error': 'حدث خطأ في التحميل',
                    'connection_error': 'خطأ في الاتصال بالخادم'
                },
                'en': {
                    'error_no_url': 'Please enter video URL',
                    'invalid_url': 'Invalid TikTok URL',
                    'download_error': 'Download error occurred',
                    'connection_error': 'Server connection error'
                }
            };

            return translations[currentLanguage]?.[key] || key;
        }

        document.addEventListener('DOMContentLoaded', function() {
            window.onclick = function(event) {
                if (event.target === resultModal || event.target === loadingModal) {
                    closeModal();
                }
            }

            if (videoUrlInput) {
                videoUrlInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        downloadVideo();
                    }
                });

                videoUrlInput.addEventListener('focus', function() {
                    this.parentElement.style.transform = 'scale(1.02)';
                });

                videoUrlInput.addEventListener('blur', function() {
                    this.parentElement.style.transform = 'scale(1)';
                });

                videoUrlInput.addEventListener('input', function() {
                    const url = this.value.trim();
                    if (url && isValidTikTokUrl(url)) {
                        this.style.borderColor = '#28a745';
                    } else if (url) {
                        this.style.borderColor = '#e74c3c';
                    } else {
                        this.style.borderColor = '';
                    }
                });
            }
        });

        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        document.addEventListener('DOMContentLoaded', function() {
            const elements = document.querySelectorAll('.feature-card, .step-item');
            elements.forEach((el) => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(50px)';
                el.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                observer.observe(el);
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    lang = session.get('lang', get_user_language())
    session['lang'] = lang
    return render_template_string(HTML_TEMPLATE, lang=lang, t=translations[lang])

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['ar', 'en']:
        session['lang'] = lang
    return redirect(url_for('index'))

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})

        if not validate_tiktok_url(url):
            return jsonify({'success': False, 'error': 'Invalid TikTok URL'})

        vd = download_tiktok_video(url)

        if vd:
            fd = {
                'nick': vd.get('nick', 'Unknown'),
                'video_info': vd.get('video_info', 'فيديو TikTok'),
                'mp4': vd.get('mp4', ''),
                'mp3': vd.get('mp3', ''),
                'video_date': vd.get('video_date', ''),
                'duration': vd.get('duration', 'غير محدد'),
                'file_size': format_file_size(vd.get('file_size', 0))
            }

            return jsonify({
                'success': True,
                'data': fd
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to fetch video data'})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Server error'})

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return render_template_string(HTML_TEMPLATE, lang=session.get('lang', 'ar'), t=translations[session.get('lang', 'ar')]), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=True,
        threaded=True
    )
