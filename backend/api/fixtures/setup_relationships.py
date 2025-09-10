"""
Script to set up many-to-many relationships between artists and labels
"""

def setup_relationships():
    from api.models import Artist, Label
    
    # Get the label
    label = Label.objects.get(id="9c8e2a60-9e3f-4e94-aa6e-c3f7d5451b8e")
    
    # Get the artists
    artist1 = Artist.objects.get(id="c7d85a49-b81e-4d28-a919-fb8b9e81c81b")  # NightRider
    artist2 = Artist.objects.get(id="e2d61a76-3d77-4f7b-be8f-d8a9e3a66c4b")  # Electron Wave
    
    # Add the label to each artist
    artist1.labels.add(label)
    artist2.labels.add(label)
    
    print(f"Added label '{label.name}' to artists: {artist1.project} and {artist2.project}")

if __name__ == "__main__":
    setup_relationships()
