# -*- coding: utf-8 -*-
"""
============================================================
 GENERIC SINGLE-FILE BUNDLER
============================================================
Recursively scans the current directory and bundles any modular
website starting from index.html into a single self-contained
HTML file.

Features:
  - Inlines iframes (via srcdoc attribute) recursively.
  - Inlines local stylesheets and script tags.
  - Converts local static images and CSS URL assets to Base64.
  - Detects dynamically referenced assets and injects a runtime
    MutationObserver-based resolver to swap paths dynamically.

============================================================
"""
import base64
import json
import os
import re
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
OUT_DIR = os.path.join(HERE, "dist")

MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
    ".avif": "image/avif", ".ico": "image/x-icon",
}

RESOLVER_TMPL = (
    "<script>(function(){\n"
    "  var assets = __ASSETS__;\n"
    "  var A = __MAP__;\n"
    "  function getAsset(key){\n"
    "    if(!key) return null;\n"
    "    var val = A[key];\n"
    "    return typeof val === 'number' ? assets[val] : null;\n"
    "  }\n"
    "  function f(r){\n"
    "    try {\n"
    "      var m = r.querySelectorAll ? r.querySelectorAll('img') : [], i;\n"
    "      for(i=0; i<m.length; i++){\n"
    "        var s = m[i].getAttribute('src');\n"
    "        var resolved = getAsset(s);\n"
    "        if(resolved) m[i].setAttribute('src', resolved);\n"
    "      }\n"
    "      var g = r.querySelectorAll ? r.querySelectorAll('image') : [];\n"
    "      for(i=0; i<g.length; i++){\n"
    "        var h = g[i].getAttribute('href') || g[i].getAttributeNS('http://www.w3.org/1999/xlink', 'href');\n"
    "        var resolved = getAsset(h);\n"
    "        if(resolved){\n"
    "          g[i].setAttribute('href', resolved);\n"
    "          try { g[i].setAttributeNS('http://www.w3.org/1999/xlink', 'href', resolved); } catch(e){}\n"
    "        }\n"
    "      }\n"
    "    } catch(e){}\n"
    "  }\n"
    "  function a(){ f(document); }\n"
    "  if(document.readyState !== 'loading') a(); else document.addEventListener('DOMContentLoaded', a);\n"
    "  try {\n"
    "    new MutationObserver(function(ms){\n"
    "      for(var i=0; i<ms.length; i++){\n"
    "        var m = ms[i];\n"
    "        if(m.type === 'attributes'){\n"
    "          var el = m.target;\n"
    "          var name = m.attributeName;\n"
    "          if(name === 'src' || name === 'href'){\n"
    "            var val = el.getAttribute(name);\n"
    "            var resolved = getAsset(val);\n"
    "            if(resolved) el.setAttribute(name, resolved);\n"
    "          }\n"
    "        } else if(m.addedNodes){\n"
    "          var n = m.addedNodes;\n"
    "          for(var k=0; k<n.length; k++){\n"
    "            var el = n[k];\n"
    "            if(el.nodeType === 1){\n"
    "              if(el.tagName === 'IMG' || el.tagName === 'image'){\n"
    "                var name = el.tagName === 'IMG' ? 'src' : 'href';\n"
    "                var val = el.getAttribute(name);\n"
    "                var resolved = getAsset(val);\n"
    "                if(resolved) el.setAttribute(name, resolved);\n"
    "              }\n"
    "              f(el);\n"
    "            }\n"
    "          }\n"
    "        }\n"
    "      }\n"
    "    }).observe(document.documentElement, {childList: true, subtree: true, attributes: true, attributeFilter: ['src', 'href']});\n"
    "  } catch(e){}\n"
    "})();</script>"
)

# Registry of files in the workspace
html_files = {}
css_files = {}
js_files = {}
asset_files = {}
processed_files = set()

def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    mime = MIME.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return "data:%s;base64,%s" % (mime, b64)

def esc_srcdoc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")

def scan_directory():
    global html_files, css_files, js_files, asset_files
    html_files = {}
    css_files = {}
    js_files = {}
    asset_files = {}
    
    for root, dirs, files in os.walk(HERE):
        # Exclude directories we don't want to bundle
        dirs[:] = [d for d in dirs if d not in ('.git', 'dist', 'node_modules', '__pycache__')]
        for file in files:
            if file in ('build.py', 'build.bat', 'bundler.html'):
                continue
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, HERE).replace('\\', '/')
            ext = os.path.splitext(file)[1].lower()
            
            if ext == '.html':
                html_files[rel_path] = read_text(path)
            elif ext == '.css':
                css_files[rel_path] = read_text(path)
            elif ext == '.js':
                js_files[rel_path] = read_text(path)
            elif ext in MIME:
                asset_files[rel_path] = {
                    "uri": data_uri(path),
                    "filename": file
                }

def inline_css_resources(css_content, css_dir):
    def replace_url(m):
        url_val = m.group(1).strip('\'"')
        if url_val.startswith(('http://', 'https://', 'data:', '//', '#')):
            return m.group(0)
        
        resolved_path = os.path.normpath(os.path.join(HERE, css_dir, url_val)).replace('\\', '/')
        rel_path = os.path.relpath(resolved_path, HERE).replace('\\', '/')
        
        if rel_path in asset_files:
            return f'url("{asset_files[rel_path]["uri"]}")'
        else:
            print(f"WARN: CSS asset not found: {url_val} (resolved: {rel_path})")
            return m.group(0)
            
    return re.sub(r'\burl\(([^)]+)\)', replace_url, css_content, flags=re.IGNORECASE)

def process_stylesheet_tags(html_content, current_dir):
    def replace_stylesheet(m):
        tag_content = m.group(1)
        if not re.search(r'\brel=["\']stylesheet["\']', tag_content, re.IGNORECASE):
            return m.group(0)
        
        href_match = re.search(r'\bhref=["\']([^"\']+)["\']', tag_content, re.IGNORECASE)
        if not href_match:
            return m.group(0)
            
        href_val = href_match.group(1)
        if href_val.startswith(('http://', 'https://', 'data:', '//')):
            return m.group(0)
            
        clean_href = href_val.split('?')[0]
        resolved_path = os.path.normpath(os.path.join(HERE, current_dir, clean_href)).replace('\\', '/')
        rel_path = os.path.relpath(resolved_path, HERE).replace('\\', '/')
        
        if rel_path in css_files:
            css_content = inline_css_resources(css_files[rel_path], os.path.dirname(rel_path))
            return f'<style>{css_content}</style>'
        else:
            print(f"WARN: local stylesheet not found: {href_val} (resolved: {rel_path})")
            return m.group(0)
            
    return re.sub(r'<link\b([^>]*?)>', replace_stylesheet, html_content, flags=re.IGNORECASE)

def process_script_tags(html_content, current_dir):
    def replace_script(m):
        tag_content = m.group(1)
        src_match = re.search(r'\bsrc=["\']([^"\']+)["\']', tag_content, re.IGNORECASE)
        if not src_match:
            return m.group(0)
            
        src_val = src_match.group(1)
        if src_val.startswith(('http://', 'https://', 'data:', '//')):
            return m.group(0)
            
        clean_src = src_val.split('?')[0]
        resolved_path = os.path.normpath(os.path.join(HERE, current_dir, clean_src)).replace('\\', '/')
        rel_path = os.path.relpath(resolved_path, HERE).replace('\\', '/')
        
        if rel_path in js_files:
            js_content = js_files[rel_path]
            js_content = re.sub(r'</script>', r'<\/script>', js_content, flags=re.IGNORECASE)
            new_attrs = re.sub(r'\bsrc=["\']([^"\']+)["\']', '', tag_content, flags=re.IGNORECASE).strip()
            attrs_str = ' ' + new_attrs if new_attrs else ''
            return f'<script{attrs_str}>{js_content}</script>'
        else:
            print(f"WARN: local script not found: {src_val} (resolved: {rel_path})")
            return m.group(0)
            
    return re.sub(r'<script\b([^>]*?)>\s*</script>', replace_script, html_content, flags=re.IGNORECASE | re.DOTALL)

def process_static_images(html_content, current_dir):
    def replace_img(m):
        tag_content = m.group(1)
        src_match = re.search(r'\bsrc=["\']([^"\']+)["\']', tag_content, re.IGNORECASE)
        if not src_match:
            return m.group(0)
        src_val = src_match.group(1)
        if src_val.startswith(('http://', 'https://', 'data:', '//')):
            return m.group(0)
        clean_src = src_val.split('?')[0]
        resolved_path = os.path.normpath(os.path.join(HERE, current_dir, clean_src)).replace('\\', '/')
        rel_path = os.path.relpath(resolved_path, HERE).replace('\\', '/')
        if rel_path in asset_files:
            new_tag = re.sub(r'\bsrc=["\']([^"\']+)["\']', f'src="{asset_files[rel_path]["uri"]}"', tag_content, flags=re.IGNORECASE)
            return f'<img{new_tag}>'
        return m.group(0)
        
    html_content = re.sub(r'<img\b([^>]*?)>', replace_img, html_content, flags=re.IGNORECASE | re.DOTALL)
    
    def replace_svg_image(m):
        tag_content = m.group(1)
        href_match = re.search(r'\b(?:xlink:)?href=["\']([^"\']+)["\']', tag_content, re.IGNORECASE)
        if not href_match:
            return m.group(0)
        href_val = href_match.group(1)
        if href_val.startswith(('http://', 'https://', 'data:', '//')):
            return m.group(0)
        clean_href = href_val.split('?')[0]
        resolved_path = os.path.normpath(os.path.join(HERE, current_dir, clean_href)).replace('\\', '/')
        rel_path = os.path.relpath(resolved_path, HERE).replace('\\', '/')
        if rel_path in asset_files:
            new_tag = re.sub(r'\b(?:xlink:)?href=["\']([^"\']+)["\']', f'href="{asset_files[rel_path]["uri"]}"', tag_content, flags=re.IGNORECASE)
            return f'<image{new_tag}>'
        return m.group(0)
        
    html_content = re.sub(r'<image\b([^>]*?)>', replace_svg_image, html_content, flags=re.IGNORECASE | re.DOTALL)
    return html_content

def process_iframe_tags(html_content, current_dir):
    def replace_iframe(m):
        tag_content = m.group(1)
        src_match = re.search(r'\bsrc=["\']([^"\']+)["\']', tag_content, re.IGNORECASE)
        if not src_match:
            return m.group(0)
        
        src_val = src_match.group(1)
        if src_val.startswith(('http://', 'https://', 'data:', '//')):
            return m.group(0)
            
        clean_src = src_val.split('?')[0]
        resolved_path = os.path.normpath(os.path.join(HERE, current_dir, clean_src)).replace('\\', '/')
        rel_path = os.path.relpath(resolved_path, HERE).replace('\\', '/')
        
        if rel_path in html_files:
            child_html = process_html(rel_path)
            srcdoc = esc_srcdoc(child_html)
            new_tag_content = re.sub(r'\bsrc=["\']([^"\']+)["\']', lambda x: f'srcdoc="{srcdoc}"', tag_content, flags=re.IGNORECASE)
            return f'<iframe{new_tag_content}>'
        else:
            print(f"WARN: local iframe src not found: {src_val} (resolved: {rel_path})")
            return m.group(0)
            
    return re.sub(r'<iframe\b([^>]*?)>', replace_iframe, html_content, flags=re.IGNORECASE | re.DOTALL)

def inject_dynamic_resolver(html_content, current_file_path):
    current_dir = os.path.dirname(current_file_path)
    assets_list = []
    assets_map = {}
    uri_to_idx = {}
    
    for rel_path, asset in asset_files.items():
        fn = asset["filename"]
        if fn in html_content:
            uri = asset["uri"]
            if uri not in uri_to_idx:
                uri_to_idx[uri] = len(assets_list)
                assets_list.append(uri)
            
            idx = uri_to_idx[uri]
            assets_map[fn] = idx
            
            rel_from_doc = os.path.relpath(rel_path, current_dir).replace('\\', '/')
            assets_map[rel_from_doc] = idx
            assets_map[rel_path] = idx
            
    if not assets_list:
        return html_content
        
    script = RESOLVER_TMPL.replace("__ASSETS__", json.dumps(assets_list)).replace("__MAP__", json.dumps(assets_map))
    
    if re.search(r'<head[^>]*>', html_content, re.IGNORECASE):
        return re.sub(r'(<head[^>]*>)', lambda m: m.group(1) + '\n' + script, html_content, count=1, flags=re.IGNORECASE)
    else:
        return script + '\n' + html_content

COORDINATORS = {
    "index.html": "index.html",
    "about/index.html": "about.html",
    "team/index.html": "team.html",
    "programs/index.html": "programs.html",
    "events/index.html": "events.html",
    "updates/index.html": "updates.html",
    "ecosystem/index.html": "ecosystem.html"
}

def parse_events_txt(path):
    if not os.path.exists(path):
        print(f"WARN: events data file not found at {path}")
        return None
    
    content = read_text(path)
    sections = re.split(r'\[(UPCOMING|RECENT)\]', content, flags=re.IGNORECASE)
    
    events = {"upcoming": [], "recent": []}
    current_key = None
    
    for i in range(1, len(sections), 2):
        key = sections[i].lower()
        part = sections[i+1].strip() if i+1 < len(sections) else ""
        if not part:
            continue
        
        blocks = part.split('---')
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.split('\n')
            ev = {}
            for line in lines:
                colon_idx = line.find(':')
                if colon_idx == -1:
                    continue
                k = line[:colon_idx].strip().lower()
                v = line[colon_idx+1:].strip()
                if k == 'date':
                    space_idx = v.find(' ')
                    if space_idx != -1:
                        ev['day'] = v[:space_idx].strip()
                        ev['monthYear'] = v[space_idx+1:].strip()
                    else:
                        ev['day'] = v
                        ev['monthYear'] = ''
                elif k == 'category':
                    ev['pill'] = v
                elif k == 'location':
                    ev['city'] = v
                elif k == 'title':
                    ev['title'] = v
                elif k == 'description':
                    ev['desc'] = v
            if 'title' in ev:
                events[key].append(ev)
    return events

def rewrite_coordinator_links(compiled_content, coord_path):
    # Rewrite href, src, to attributes pointing to coordinator index.html pages
    def repl_attr(match):
        attr_name = match.group(1)
        quote = match.group(2)
        path_val = match.group(3)
        
        parts = path_val.split('#', 1)
        base_path = parts[0]
        hash_part = '#' + parts[1] if len(parts) > 1 else ''
        
        parts2 = base_path.split('?', 1)
        clean_path = parts2[0]
        query_part = '?' + parts2[1] if len(parts2) > 1 else ''
        
        coord_dir = os.path.dirname(coord_path)
        combined = os.path.normpath(os.path.join(coord_dir, clean_path)).replace('\\', '/')
        if combined.startswith('./'):
            combined = combined[2:]
        if combined.startswith('/'):
            combined = combined[1:]
            
        if combined in COORDINATORS:
            target = COORDINATORS[combined]
            new_path = target + query_part + hash_part
            return f"{attr_name}={quote}{new_path}{quote}"
            
        return match.group(0)

    compiled_content = re.sub(r'\b(href|src|to)\s*=\s*(["\'])([^"\']*?\bindex\.html.*?)\2', repl_attr, compiled_content, flags=re.IGNORECASE)
    
    # Also rewrite to: 'about/index.html' in JS object format
    def repl_js_prop(match):
        prop_name = match.group(1)
        quote = match.group(2)
        path_val = match.group(3)
        
        coord_dir = os.path.dirname(coord_path)
        combined = os.path.normpath(os.path.join(coord_dir, path_val)).replace('\\', '/')
        if combined.startswith('./'):
            combined = combined[2:]
        if combined.startswith('/'):
            combined = combined[1:]
            
        if combined in COORDINATORS:
            target = COORDINATORS[combined]
            return f"{prop_name}:{quote}{target}{quote}"
            
        return match.group(0)

    compiled_content = re.sub(r'\b(to)\s*:\s*(["\'])([^"\']*?\bindex\.html.*?)\2', repl_js_prop, compiled_content, flags=re.IGNORECASE)
    
    return compiled_content

def process_html(html_file_path):
    if html_file_path in processed_files:
        return ""
    processed_files.add(html_file_path)
    
    content = html_files[html_file_path]
    current_dir = os.path.dirname(html_file_path)
    
    # Inline parsed events text database for events section
    if html_file_path == "events/sections/01-events.html":
        events_txt_path = os.path.join(HERE, "events", "events_data.txt")
        events_data = parse_events_txt(events_txt_path)
        if events_data:
            print(f"Inlining parsed events data into {html_file_path}...")
            content = content.replace("let EVENTS = null;", f"let EVENTS = {json.dumps(events_data, ensure_ascii=False)};")
    
    content = process_stylesheet_tags(content, current_dir)
    content = process_script_tags(content, current_dir)
    content = process_static_images(content, current_dir)
    content = inject_dynamic_resolver(content, html_file_path)
    content = process_iframe_tags(content, current_dir)
    
    processed_files.remove(html_file_path)
    return content

def main():
    print("Scanning workspace files...")
    scan_directory()
    
    os.makedirs(OUT_DIR, exist_ok=True)
    
    for coord_path, target_filename in COORDINATORS.items():
        if coord_path not in html_files:
            print(f"ERROR: Coordinator file {coord_path} not found in workspace!")
            continue
            
        print(f"Compiling coordinator {coord_path} -> {target_filename}...")
        
        # Clear recursion registry for each coordinator
        processed_files.clear()
        
        compiled_html = process_html(coord_path)
        compiled_html = rewrite_coordinator_links(compiled_html, coord_path)
        
        out_file = os.path.join(OUT_DIR, target_filename)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(compiled_html)
            
        size_mb = os.path.getsize(out_file) / (1024 * 1024)
        print(f"  Compiled {target_filename} ({size_mb:.2f} MB)")
        
    print("=" * 64)
    print("  Multi-page Single-file build complete.")
    print("  Output Directory: %s" % OUT_DIR)
    print("=" * 64)

    try:
        index_out = os.path.join(OUT_DIR, "index.html")
        webbrowser.open("file:///" + index_out.replace("\\", "/"))
    except Exception:
        pass

if __name__ == "__main__":
    main()
