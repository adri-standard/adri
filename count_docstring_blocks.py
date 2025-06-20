from tests.documentation.utils.code_extractor import CodeExtractor
import os

total_blocks = 0
docstring_blocks = 0

for root, dirs, files in os.walk('docs'):
    for file in files:
        if file.endswith('.md'):
            filepath = os.path.join(root, file)
            try:
                blocks = CodeExtractor.extract_from_markdown(filepath)
                file_docstring_blocks = [b for b in blocks if any(marker in b.context for marker in ['Example:', 'def '])]
                total_blocks += len(blocks)
                docstring_blocks += len(file_docstring_blocks)
                if file_docstring_blocks:
                    print(f'{filepath}: {len(file_docstring_blocks)} docstring blocks')
            except Exception as e:
                print(f'Error processing {filepath}: {e}')

print(f'Total blocks: {total_blocks}')
print(f'Docstring blocks: {docstring_blocks}')
