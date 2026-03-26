import os
import re

def update_templates():
    template_dir = 'templates'
    
    # 1. Regex for removing dash-sidebar-logo
    # This matches <div class="dash-sidebar-logo"> ... </div>
    logo_re = re.compile(r'<div class="dash-sidebar-logo">.*?</div>', re.DOTALL)
    
    # 2. Regex for injecting nav-label into dash-sidebar-item
    # It captures the opening div (which contains title="..."), the <i> tag, and the closing div.
    item_re = re.compile(r'(<div class="dash-sidebar-item[^>]*title="([^"]+)"[^>]*>)\s*(<i data-lucide="[^"]+"[^>]*></i>)\s*(</div>)', re.DOTALL)
    
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if it has a dash-sidebar
                if 'dash-sidebar' in content:
                    new_content = logo_re.sub('', content)
                    
                    def replacer(match):
                        open_div = match.group(1)
                        title = match.group(2)
                        i_tag = match.group(3)
                        close_div = match.group(4)
                        return f'{open_div}\n        {i_tag}\n        <span class="nav-label">{title}</span>\n      {close_div}'
                        
                    new_content = item_re.sub(replacer, new_content)
                    
                    # Remove any empty <!-- Logo --> comments if left behind
                    new_content = new_content.replace('<!-- Logo -->\n    \n', '')
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated {file}")

if __name__ == '__main__':
    update_templates()
