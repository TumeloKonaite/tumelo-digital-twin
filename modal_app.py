import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir("src", remote_path="/root/src")
    .add_local_dir("data", remote_path="/root/data")
    .add_local_file("main.py", remote_path="/root/main.py")
)

app = modal.App("digital-twin-api", image=image)


@app.function(
    min_containers=0,
    max_containers=2,
    secrets=[modal.Secret.from_name("digital-twin-api-secrets")],
)
@modal.asgi_app()
def fastapi_app():
    from main import app as fastapi_app

    return fastapi_app
