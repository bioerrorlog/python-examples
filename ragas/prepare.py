import wikipedia


def save_wikipedia_page(title, filename):
    try:
        page = wikipedia.page(title)
        content = page.content

        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Page '{title}' has been saved to '{filename}'.")
    except wikipedia.exceptions.PageError:
        print("Error: The page could not be found.")
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"Error: The page name is ambiguous. Possible pages are: {e.options}")
    except Exception as e:
        print(f"An error occurred: {e}")


save_wikipedia_page("Generative pre-trained transformer", "data/gpt.txt")
save_wikipedia_page("Large language model", "data/llm.txt")
