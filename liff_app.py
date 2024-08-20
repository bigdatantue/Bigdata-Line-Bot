from map import LIFFSize
from flask import Blueprint, request, render_template

liff_app = Blueprint('liff_app', __name__)

# ----------------LIFF 三種尺寸跳轉用頁面(勿動) Start----------------

@liff_app.route('/full', methods=['GET'])
def full():
    liff_id = LIFFSize.FULL.value
    return render_template('liff/liff.html', liff_id=liff_id)

@liff_app.route('/tall', methods=['GET'])
def tall():
    liff_id = LIFFSize.TALL.value
    return render_template('liff/liff.html', liff_id=liff_id)

@liff_app.route('/compact', methods=['GET'])
def compact():
    liff_id = LIFFSize.COMPACT.value
    return render_template('liff/liff.html', liff_id=liff_id)

# ----------------LIFF 三種尺寸跳轉用頁面(勿動) End----------------

# ----------------LIFF 頁面(根據需求設定不同大小) Start----------------
@liff_app.route('/tall/userinfo', methods=['GET'])
def userinfo():
    liff_id = LIFFSize.TALL.value
    return render_template('liff/userinfo.html', **locals())

# ----------------LIFF 頁面(根據需求設定不同大小) End----------------
