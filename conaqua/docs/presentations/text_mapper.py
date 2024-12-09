from bs4 import BeautifulSoup
import os

# Path to the HTML file
html_file_path = "conacua.html"
# Path to the output text file
output_file_path = "conacua_parsed.txt"

# Function to parse the HTML and extract tag, location, and content without src, style, or script references
def parse_html(html_path, output_path):
    # Read the HTML file
    with open(html_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # Open the output file to write the parsed content
    with open(output_path, "w", encoding="utf-8") as output_file:
        for tag in soup.find_all(True):  # Iterate over all tags in the HTML
            # Skip tags that contain 'src' attributes or are 'style' or 'script' tags to avoid large references, CSS, and scripts
            if 'src' in tag.attrs or tag.name in ['style', 'script']:
                continue

            # Get the tag name, attributes, and the text content
            tag_name = tag.name
            tag_content = tag.get_text(strip=True)
            tag_attributes = {k: v for k, v in tag.attrs.items() if k != 'src'}
            tag_location = tag.sourceline  # Get the source line of the tag

            # Clean up the content by removing excess whitespace
            cleaned_content = ' '.join(tag_content.split())

            # Write the details to the output file
            output_file.write(f"Tag: {tag_name}, Location: {tag_location}\n")
            if tag_attributes:
                output_file.write(f"Attributes: {tag_attributes}\n")
            output_file.write(f"Content: {cleaned_content}\n\n")

if __name__ == "__main__":
    # Activate the virtual environment (using os.system to run a shell command)
    os.system("source ~/Dev/environments/data-analysis/bin/activate")

    # Parse the HTML and save to output file
    parse_html(html_file_path, output_file_path)
    print(f"Parsed content saved to {output_file_path}")
