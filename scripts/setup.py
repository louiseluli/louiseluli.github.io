#!/usr/bin/env python3
"""
Setup Helper Script
Helps you quickly configure your portfolio with your information
"""

import json
import sys
from pathlib import Path

def load_config():
    """Load config.json"""
    config_path = Path('config.json')
    if not config_path.exists():
        print("❌ config.json not found!")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """Save config.json"""
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def update_personal_info(config):
    """Update personal information"""
    print("\n" + "="*60)
    print("📝 PERSONAL INFORMATION")
    print("="*60)
    print("Press Enter to keep current value")
    print()
    
    # Name
    current_name = config['personal']['name']
    new_name = input(f"Name [{current_name}]: ").strip()
    if new_name:
        config['personal']['name'] = new_name
    
    # Email
    current_email = config['personal']['email']
    new_email = input(f"Email [{current_email}]: ").strip()
    if new_email:
        config['personal']['email'] = new_email
    
    # GitHub
    current_github = config['personal']['github']
    new_github = input(f"GitHub URL [{current_github}]: ").strip()
    if new_github:
        config['personal']['github'] = new_github
    
    # LinkedIn
    current_linkedin = config['personal']['linkedin']
    new_linkedin = input(f"LinkedIn URL [{current_linkedin}]: ").strip()
    if new_linkedin:
        config['personal']['linkedin'] = new_linkedin
    
    print("\n✅ Personal information updated!")
    return config

def update_colors(config):
    """Update theme colors"""
    print("\n" + "="*60)
    print("🎨 THEME COLORS")
    print("="*60)
    print("Enter hex colors (e.g., #8B5CF6) or press Enter to skip")
    print()
    
    # Primary Color
    current_primary = config['theme']['primary_color']
    new_primary = input(f"Primary Color [{current_primary}]: ").strip()
    if new_primary and new_primary.startswith('#'):
        config['theme']['primary_color'] = new_primary
    
    # Secondary Color
    current_secondary = config['theme']['secondary_color']
    new_secondary = input(f"Secondary Color [{current_secondary}]: ").strip()
    if new_secondary and new_secondary.startswith('#'):
        config['theme']['secondary_color'] = new_secondary
    
    print("\n✅ Theme colors updated!")
    return config

def generate_git_commands(config):
    """Generate git deployment commands"""
    name = config['personal']['name'].lower().replace(' ', '')
    github_username = config['personal']['github'].split('/')[-1]
    
    print("\n" + "="*60)
    print("🚀 DEPLOYMENT COMMANDS")
    print("="*60)
    print("\nRun these commands to deploy your portfolio:")
    print()
    print(f"# 1. Create repository on GitHub: {github_username}.github.io")
    print()
    print("# 2. Run these commands:")
    print("git init")
    print("git add .")
    print('git commit -m "🚀 Launch portfolio"')
    print(f"git remote add origin https://github.com/{github_username}/{github_username}.github.io.git")
    print("git branch -M main")
    print("git push -u origin main")
    print()
    print(f"# 3. Enable GitHub Pages in repository settings")
    print()
    print(f"# 4. Your site will be live at:")
    print(f"   https://{github_username}.github.io")
    print("="*60)

def main():
    """Main setup wizard"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           Portfolio Setup Helper                        ║
    ║           Quick configuration wizard                     ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Load config
    print("📂 Loading configuration...")
    config = load_config()
    print("✅ Configuration loaded!")
    
    # Main menu
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("1. Update personal information")
        print("2. Update theme colors")
        print("3. Show deployment commands")
        print("4. Save and exit")
        print("5. Exit without saving")
        
        choice = input("\nChoice [1-5]: ").strip()
        
        if choice == '1':
            config = update_personal_info(config)
        elif choice == '2':
            config = update_colors(config)
        elif choice == '3':
            generate_git_commands(config)
        elif choice == '4':
            save_config(config)
            print("\n✅ Configuration saved to config.json!")
            generate_git_commands(config)
            print("\n🎉 Setup complete! Your portfolio is ready to deploy!")
            break
        elif choice == '5':
            print("\n❌ Exiting without saving...")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")
    
    print("\n" + "="*60)
    print("Thank you for using Portfolio Setup Helper!")
    print("="*60)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)