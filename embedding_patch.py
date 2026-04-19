from mem0.embeddings.ollama import OllamaEmbedding

from config import TARGET_EMBEDDING_DIM


def install_ollama_embedding_padding_patch(target_dim=TARGET_EMBEDDING_DIM):
    if getattr(OllamaEmbedding.embed, "_padding_patch_installed", False):
        return False

    original_embed = OllamaEmbedding.embed

    def patched_embed(self, text, *args, **kwargs):
        try:
            vector = original_embed(self, text, *args, **kwargs)
        except TypeError:
            vector = original_embed(self, text)

        current_dim = len(vector)
        if current_dim < target_dim:
            return vector + [0.0] * (target_dim - current_dim)
        return vector

    patched_embed._padding_patch_installed = True
    patched_embed._original_embed = original_embed
    OllamaEmbedding.embed = patched_embed
    return True
