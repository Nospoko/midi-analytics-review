import pandas as pd
import fortepyan as ff
import streamlit as st
from fortepyan import MidiFile, MidiPiece
from fortepyan.analytics.clustering import process as clustering_process


def main():
    uploaded_file = st.file_uploader("Choose a file", type=["midi", "mid"])

    if uploaded_file is not None:
        piece = MidiFile(uploaded_file).piece

        # TODO Document what the *n* parameter is doing
        n_clustering = st.number_input(label="n parameter", value=16)
        df = clustering_process.run(piece, n=n_clustering)
        fragments = prepare_fragments(df=df, piece=piece, n=n_clustering)

        st.markdown("## Summary")
        n_fragments = len(fragments)
        st.markdown(f"Detected: {n_fragments} fragments")

        for it, fragment in enumerate(fragments):
            st.markdown(f"### Fragment {it}")

            variants = fragment["variants"]
            n_variants = len(variants)
            st.markdown(f"This fragment has {n_variants} variants")

            variant = variants[0]
            start = variant["start_note_index"]
            finish = variant["finish_note_index"]
            part_piece = piece[start:finish]

            st.markdown("Showing a pianoroll for one of the variants")
            st.markdown(f"This variant has {part_piece.size} notes and {part_piece.duration:.2f} seconds")

            fig = ff.view.draw_pianoroll_with_velocities(part_piece)
            st.pyplot(fig, clear_figure=True)


def prepare_fragments(df: pd.DataFrame, piece: MidiPiece, n: int) -> list[dict]:
    # Unpack
    fragments = []
    for it, row in df.iterrows():
        variants = []
        for idx in row.idxs:
            start_idx = idx - row.left_shift
            start_idx = max(start_idx, 0)
            start_time = piece.df.iloc[start_idx].start

            finish_idx = idx + row.right_shift + n
            finish_idx = min(finish_idx, piece.size - 1)
            finish_time = piece.df.iloc[finish_idx].end

            variant = dict(
                start_time=start_time,
                finish_time=finish_time,
                start_note_index=int(start_idx),
                finish_note_index=int(finish_idx),
            )
            variants.append(variant)
        fragment = dict(variants=variants)
        fragments.append(fragment)

    return fragments


if __name__ == "__main__":
    main()
