import os

import pandas as pd
import fortepyan as ff
import streamlit as st
from fortepyan import MidiFile, MidiPiece
from fortepyan.audio import render as render_audio
from fortepyan.analytics.clustering import process as clustering_process


def generated_piece_av(piece: MidiPiece, save_base: str) -> dict:
    mp3_path = save_base + ".mp3"

    if not os.path.exists(mp3_path):
        render_audio.midi_to_mp3(piece.to_midi(), mp3_path)

    pianoroll_path = save_base + "-pr.png"

    midi_path = save_base + ".mid"
    input_path = save_base + "-input.mid"
    output_path = save_base + "-output.mid"

    paths = {
        "mp3": mp3_path,
        "midi": midi_path,
        "pianoroll": pianoroll_path,
        "input_midi": input_path,
        "output_midi": output_path,
    }
    return paths


def main():
    uploaded_file = st.file_uploader("Choose a file", type=["midi", "mid"])

    if uploaded_file is not None:
        piece = MidiFile(uploaded_file).piece
        st.markdown("### Showing a pianoroll of the uploaded MIDI file")
        fig = ff.view.draw_pianoroll_with_velocities(piece)
        st.pyplot(fig, clear_figure=True)

        generated_piece_av(piece, "uploaded_file")
        st.audio("uploaded_file.mp3")

        n_clustering = st.number_input(label="N parameter:", value=16)
        st.markdown("The N parameter specifies how many consecutive pitch values are used to distinguish identical fragments")
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

            generated_piece_av(part_piece, "part_piece")
            st.audio("part_piece.mp3")


def prepare_fragments(df: pd.DataFrame, piece: MidiPiece, n: int) -> list[dict]:
    # Filter fragments with most variants (top 5)
    df = df.nlargest(5, "n_variants")

    fragments = []
    max_fragments = 5
    max_variants = 5

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

            # Filter out fragments with long pauses
            max_pause_duration = 2.0
            if finish_time - start_time > max_pause_duration:
                if len(variants) >= max_variants:
                    break

        if len(variants) > 0:
            fragment = dict(variants=variants)
            fragments.append(fragment)

        if len(fragments) >= max_fragments:
            break

    return fragments


if __name__ == "__main__":
    main()
