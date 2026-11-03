"""
Patches the Devanagari notebook to add model.save() at the end.
Run once from the Mini project folder:  python add_save_cell.py
"""
import json, os, sys

NOTEBOOK = os.path.join(os.path.dirname(__file__), "Devangiri_Resnet_Revnet_topology.ipynb")

with open(NOTEBOOK, "r", encoding="utf-8") as f:
    nb = json.load(f)

SAVE_SOURCE = [
    "# Save the trained model so the Flask backend can load it\n",
    "model.save('devanagari_resnet18.h5')\n",
    "print('Model saved to devanagari_resnet18.h5')\n",
    "# Download from Colab: Files → devanagari_resnet18.h5\n",
    "# Then copy it to the backend/ folder of the Mini project.\n",
]

# Check if save cell already exists
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        if "devanagari_resnet18.h5" in src:
            print("Save cell already present — nothing to do.")
            sys.exit(0)

# Append new code cell
new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {"id": "save_model_cell"},
    "outputs": [],
    "source": SAVE_SOURCE,
}
nb["cells"].append(new_cell)

with open(NOTEBOOK, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Added model save cell to: {NOTEBOOK}")
print("Open the notebook and run the new last cell after training to save the model.")
