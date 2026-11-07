import numpy as np
import torch
from torch import nn

WINDOW = 12
SCALE = 20.0


class DemandLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.recurrent = nn.LSTM(1, 12, batch_first=True)
        self.output = nn.Linear(12, 1)

    def forward(self, values):
        encoded, _ = self.recurrent(values)
        return self.output(encoded[:, -1, :]).squeeze(-1)


def train(directory):
    torch.manual_seed(7)
    torch.set_num_threads(1)
    rng = np.random.default_rng(7)
    t = np.arange(720)
    values = np.clip(8 + 4 * np.sin(t * 2 * np.pi / 72) + rng.normal(0, .7, len(t)), 0, None)
    windows = np.lib.stride_tricks.sliding_window_view(values, WINDOW + 1)
    x = torch.tensor(windows[:, :-1, None] / SCALE, dtype=torch.float32)
    y = torch.tensor(windows[:, -1] / SCALE, dtype=torch.float32)
    split = int(len(x) * .8)
    model = DemandLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=.015)
    for _ in range(75):
        optimizer.zero_grad()
        loss = nn.functional.mse_loss(model(x[:split]), y[:split])
        loss.backward()
        optimizer.step()
    with torch.inference_mode():
        predictions = model(x[split + WINDOW:]) * SCALE
        mae = (predictions - y[split + WINDOW:] * SCALE).abs().mean().item()
    torch.save(model.state_dict(), directory / "demand.pt")
    return {"forecast_mae": round(mae, 4), "seed_window": values[-WINDOW:].tolist()}


def load(directory):
    torch.set_num_threads(1)
    model = DemandLSTM()
    model.load_state_dict(torch.load(directory / "demand.pt", map_location="cpu", weights_only=True))
    return model.eval()


def predict(model, counts):
    with torch.inference_mode():
        x = torch.tensor(counts, dtype=torch.float32).reshape(1, WINDOW, 1) / SCALE
        return max(0.0, float(model(x).item() * SCALE))
