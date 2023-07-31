from typing import Tuple, Union

import torch
import torch.nn as nn
import torchaudio.transforms as transforms
from torchaudio_augmentations import (
    Compose,
    Delay,
    Gain,
    Noise,
    PitchShift,
    Reverb,
    PolarityInversion,
    RandomApply,
    RandomResizedCrop,
    HighLowPass,
)


def get_transforms(
    args,
):
    transform = Compose(
        [
            RandomApply([PolarityInversion()], p=0.8),
            RandomApply([Noise()], p=0.01),
            RandomApply([Gain()], p=0.3),
            RandomApply([HighLowPass(sample_rate=args.sample_rate)], p=0.8),
            RandomApply([Delay(sample_rate=args.sample_rate)], p=0.3),
            RandomApply(
                [PitchShift(n_samples=args.n_samples, sample_rate=args.sample_rate)],
                p=0.6,
            ),
            RandomApply([Reverb(sample_rate=args.sample_rate)], p=0.6),
        ]
    )
    return transform


class AudioSplit(nn.Module):
    def __init__(
        self,
        args,
    ):
        super().__init__()
        self.split = RandomResizedCrop(n_samples=args.n_samples)
        self.transforms = get_transforms(args)
        self.mel = transforms.MelSpectrogram(
            n_fft=args.n_fft,
            win_length=args.win_length,
            hop_length=args.hop_length,
            f_min=args.f_min,
            f_max=args.f_max,
            sample_rate=args.sample_rate,
        )

    @torch.no_grad()
    def forward(self, waveform: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        waveform1 = self.split(waveform)
        waveform2 = self.split(waveform)
        if self.transforms is not None:
            waveform1 = self.transforms(waveform1)
            waveform2 = self.transforms(waveform2)
        melspec1 = self.mel(waveform1)
        melspec1 = torch.stack([melspec1, melspec1, melspec1], dim=0).squeeze()
        melspec2 = self.mel(waveform2)
        melspec2 = torch.stack([melspec2, melspec2, melspec2], dim=0).squeeze()
        return melspec1, melspec2