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
        file_name = uploaded_file.name.replace(".mid", "")

        piece = MidiFile(uploaded_file).piece
        st.markdown("### Showing a pianoroll of the uploaded MIDI file")
        fig = ff.view.draw_pianoroll_with_velocities(piece)
        st.pyplot(fig, clear_figure=True)

        if not os.path.isdir(f"tmp/{file_name}"):
            os.mkdir(f"tmp/{file_name}")

        original_paths = generated_piece_av(piece, f"tmp/{file_name}/{file_name}")
        st.audio(original_paths["mp3"])

        n_clustering = 16
        st.markdown("The N parameter specifies how many consecutive pitch values are used to distinguish identical fragments")

        df = clustering_process.run(piece, n=n_clustering)
        fragments = prepare_fragments(df=df, piece=piece, n=n_clustering)

        filtering_method = st.selectbox(
            label="Filtering method",
            options=["Top 5", "Fastest", "Longest"],
        )

        st.markdown("## Summary")
        n_fragments = len(fragments)
        st.markdown(f"Detected: {n_fragments} fragments")

        if filtering_method == "Top 5":
            filtered_fragments = top_five_filtering(fragments)
        elif filtering_method == "Fastest":
            filtered_fragments = fastest_filtering(fragments)
        elif filtering_method == "Longest":
            filtered_fragments = longest_filtering(fragments)
        else:
            raise ValueError(f"Unknown filtering method: {filtering_method}")

        st.markdown("## Filtered Fragments")
        for it, fragment in enumerate(filtered_fragments):
            st.markdown(f"### Filtered Fragment {it}")
            n_variants = len(fragment)
            st.markdown(f"This fragment has {n_variants} variants")
            for it_v, variant in enumerate(fragment):
                start = variant["start_note_index"]
                finish = variant["finish_note_index"]
                part_piece = piece[start:finish]

                st.markdown("Showing a pianoroll for one of the variants")
                st.markdown(f"This variant has {part_piece.size} notes and {part_piece.duration:.2f} seconds")

                fig = ff.view.draw_pianoroll_with_velocities(part_piece)
                st.pyplot(fig, clear_figure=True)

                paths = generated_piece_av(part_piece, f"tmp/{file_name}/{filtering_method}-f{it}-v{it_v}")
                st.audio(paths["mp3"])


def top_five_filtering(fragments: list[list[dict]]):
    return fragments[:5]


def fastest_filtering(fragments: list[list[dict]]):
    return sorted(fragments, key=lambda x: sum(v["finish_time"] - v["start_time"] for v in x))[:5]


def longest_filtering(fragments: list[list[dict]]):
    return sorted(fragments, key=lambda x: sum(v["finish_time"] - v["start_time"] for v in x), reverse=True)[:5]


def prepare_fragments(df: pd.DataFrame, piece: MidiPiece, n: int) -> list[list[dict]]:
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

            variant = {
                "start_time": start_time,
                "finish_time": finish_time,
                "start_note_index": start_idx,
                "finish_note_index": finish_idx,
            }
            variants.append(variant)
        fragments.append(variants)

    return fragments


if __name__ == "__main__":
    main()
