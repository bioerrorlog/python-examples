from langchain.document_loaders import DirectoryLoader


loader = DirectoryLoader("data/")
documents = loader.load()
