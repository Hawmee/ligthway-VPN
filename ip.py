#!/usr/bin/env python3
"""
Minimal IP address replacement script
"""

from pathlib import Path
import configparser
import os

def main():
    # Get IP address from user
    ip = input("IP address to use: ").strip()
    
    # Paths
    script_dir = Path(__file__).parent
    template_dir = script_dir / "template"
    generate_dir = script_dir / "generate"
    
    # Create default output directory
    generate_dir.mkdir(exist_ok=True)
    
    # Check if template directory exists
    if not template_dir.exists():
        print("[-] Error: template directory does not exist")
        return
    
    # Check if template directory has files
    template_files = [f for f in template_dir.iterdir() if f.is_file()]
    if not template_files:
        print("[!] No files found in template directory")
        return
    
    # Read destination paths from dir.conf if it exists
    destination_paths = {}
    dir_conf = template_dir / "dir.conf"
    
    if dir_conf.exists():
        try:
            config = configparser.ConfigParser()
            # Preserve case sensitivity
            config.optionxform = lambda option: option  # This preserves original case
            config.read(dir_conf)
            
            if 'destinationPath' in config:
                for template_filename, path in config['destinationPath'].items():
                    # Remove .template extension from filename for destination
                    output_filename = template_filename.replace('.template', '')
                    # Convert relative path to absolute path relative to script
                    abs_path = script_dir / path
                    # Ensure it's a directory path, then add filename
                    if not abs_path.suffix or abs_path.suffix == path:  # If it looks like a directory
                        abs_path = abs_path / output_filename
                    destination_paths[template_filename] = abs_path
                    print(f"[+] {template_filename} -> {abs_path}")
                    
        except Exception as e:
            print(f"[-] Error reading dir.conf: {e}")
    
    print(f"[+] Processing templates with IP: {ip}")
    
    # Process each template file (skip dir.conf)
    for template_file in template_files:
        if template_file.name == "dir.conf":
            continue
            
        try:
            # Read and modify
            content = template_file.read_text(encoding='utf-8')
            content = content.replace("{ip_addr}", ip)
            
            # Determine output path - remove .template extension
            if template_file.name in destination_paths:
                output_path = destination_paths[template_file.name]
            else:
                # Remove .template extension for default destination
                output_filename = template_file.name.replace('.template', '')
                output_path = generate_dir / output_filename
            
            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write new file
            output_path.write_text(content, encoding='utf-8')
            
            print(f"[+] {template_file.name} -> {output_path}")
            
        except UnicodeDecodeError:
            print(f"[-] Skipping binary file: {template_file.name}")
        except Exception as e:
            print(f"[-] Error processing {template_file.name}: {e}")
    
    print("[+] All files processed")

if __name__ == "__main__":
    main()