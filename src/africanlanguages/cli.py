from cyclopts import App

app = App()


@app.command()
def main():
    print("This is the main entrypoint")


if __name__ == "__main__":
    app()
