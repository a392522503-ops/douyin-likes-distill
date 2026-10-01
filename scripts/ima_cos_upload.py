#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ima 知识库入库第二步：把本地文件按 create_media 返回的临时凭证上传到 COS。

用法（cred json 由 create_media 返回的 cos_credential + cos_key 拼成）：
  python ima_cos_upload.py <cred_json_file> <local_file_path>

cred_json 结构示例：
{
  "cos_credential": {
     "token": "...", "secret_id": "...", "secret_key": "...",
     "start_time": "1790649291", "expired_time": "1790692491",
     "bucket_name": "xxx-1258344701", "region": "ap-shanghai"
  },
  "cos_key": "2/Pykb.../file_manager/xxx.md"
}

成功打印 OK:<size>，失败打印 ERR:<msg> 并以非 0 退出。
"""
import sys
import json
import hmac
import hashlib
import time
import urllib.parse
import urllib.request
import urllib.error

MIME_MAP = {
    "md": "text/markdown",
    "markdown": "text/markdown",
    "txt": "text/plain",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "html": "text/html",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/x-m4a",
}


def enc(s):
    return urllib.parse.quote(s, safe="-_.~")


def build_authorization(secret_id, secret_key, method, key, headers, sign_time):
    start, end = sign_time.split(";")
    key_time = sign_time
    sign_key = hmac.new(secret_key.encode("utf-8"), key_time.encode("utf-8"), hashlib.sha1).hexdigest()

    header_keys = sorted(k.lower() for k in headers.keys())
    header_list = ";".join(header_keys)
    header_pairs = []
    for k in header_keys:
        real_key = [kk for kk in headers if kk.lower() == k][0]
        header_pairs.append("{}={}".format(enc(k), enc(str(headers[real_key]))))
    http_headers = "&".join(header_pairs)
    key_to_sign = "/" + key
    http_string = "\n".join([method.lower(), key_to_sign, "", http_headers, ""])
    string_to_sign = "sha1\n{}\n{}\n".format(key_time, hashlib.sha1(http_string.encode("utf-8")).hexdigest())
    signature = hmac.new(sign_key.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1).hexdigest()

    return (
        "q-sign-algorithm=sha1"
        "&q-ak={}".format(secret_id)
        + "&q-sign-time={}".format(sign_time)
        + "&q-key-time={}".format(key_time)
        + "&q-header-list={}".format(header_list)
        + "&q-url-param-list="
        + "&q-signature={}".format(signature)
    )


def main():
    if len(sys.argv) < 3:
        print("ERR: usage")
        sys.exit(2)
    cred_file, local_file = sys.argv[1], sys.argv[2]

    with open(cred_file, "r", encoding="utf-8") as f:
        payload = json.load(f)
    cred = payload["cos_credential"]
    cos_key = payload["cos_key"]

    ext = local_file.rsplit(".", 1)[-1].lower()
    content_type = MIME_MAP.get(ext)
    if not content_type:
        print("ERR: unknown ext {}".format(ext))
        sys.exit(2)

    with open(local_file, "rb") as f:
        data = f.read()

    host = "{}.cos.{}.myqcloud.com".format(cred["bucket_name"], cred["region"])
    url = "https://{}/{}".format(host, urllib.parse.quote(cos_key, safe="/"))

    headers_to_sign = {
        "host": host,
        "x-cos-security-token": cred["token"],
    }
    sign_time = "{};{}".format(cred["start_time"], cred["expired_time"])
    auth = build_authorization(cred["secret_id"], cred["secret_key"], "put", cos_key, headers_to_sign, sign_time)

    headers = {
        "Host": host,
        "Authorization": auth,
        "x-cos-security-token": cred["token"],
        "Content-Type": content_type,
        "Content-Length": str(len(data)),
    }

    req = urllib.request.Request(url, data=data, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
            print("OK:{}".format(resp.status))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")[:500]
        except Exception:
            pass
        print("ERR:http{} {}".format(e.code, body))
        sys.exit(3)
    except Exception as e:
        print("ERR:{}".format(e))
        sys.exit(4)


if __name__ == "__main__":
    main()
