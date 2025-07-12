# govee-lan-api-plus/setup.py

from setuptools import setup, find_packages

setup(
    name="govee_lan_api_plus",
    version="0.1",
    description="Control Govee DIY scenes over LAN using pre-captured MQTT payloads.",
    author="Jimmy Hickman",
    packages=find_packages(exclude=["tests", "venv", "logs", "assets", ".github"]),
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.7",
)