from setuptools import setup, find_packages

setup(
    name="api_dungeon",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "setuptools==77.0.3",
        "wheel==0.45.1",
        "mypy==1.15.0",
        "typing-extensions==4.12.2",
        "Pillow==11.1.0",
        "google-generativeai==0.8.4",
        "openai==1.68.2",
        "python-dotenv==1.0.1",
        "SQLAlchemy==2.0.39",
        "requests==2.32.3"
    ],
) 