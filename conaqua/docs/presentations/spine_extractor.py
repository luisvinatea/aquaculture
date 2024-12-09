from bs4 import BeautifulSoup

# Open the HTML file
with open('conacua.html', 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file, 'html.parser')

# Recursive function to build the spine
def get_html_spine(tag, level=0, file=None):
    if tag.name:
        line = '  ' * level + tag.name
        if file:
            file.write(line + '\n')
        else:
            print(line)  # Print tag with indentation
        for child in tag.children:
            get_html_spine(child, level + 1, file)

# Start from the root of the document and print to console
get_html_spine(soup)

# Save output to a file 
with open('spine.txt', 'w', encoding='utf-8') as file:
    get_html_spine(soup, file=file)