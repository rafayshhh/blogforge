"""Unit tests verifying anti-AI-slop heuristics, cliché detection, and scoring."""

from app.generation.reviewer import (
    detect_ai_cliches,
    detect_repeated_ngrams,
)


def test_anti_slop_cliche_detection():
    slop_text = (
        "In today's fast-paced digital world, it is important to remember that microservices "
        "stand as a testament to modern engineering. Let us delve into the rich tapestry of distributed "
        "systems and dive deep into how they seamlessly integrate. This is a game-changer and a true "
        "paradigm shift in the realm of cloud architecture. Let's unpack the panacea."
    )
    cliches = detect_ai_cliches(slop_text)
    assert len(cliches) >= 5
    assert any("fast-paced" in c.lower() for c in cliches)
    assert any("delve" in c.lower() for c in cliches)
    assert any("tapestry" in c.lower() for c in cliches)
    assert any("game-changer" in c.lower() for c in cliches)
    assert any("realm of" in c.lower() for c in cliches)


def test_human_authored_text_zero_cliches():
    clean_technical_text = (
        "Under high network load, Linux socket buffers experience kernel packet drops when the "
        "receive queue exceeds 1,024 packets. By tuning net.core.rmem_max to 16MB and adopting "
        "eBPF ring buffers, system throughput increased by 42% while p99 latency remained capped at 18ms."
    )
    cliches = detect_ai_cliches(clean_technical_text)
    assert len(cliches) == 0


def test_repeated_ngrams_detection():
    repetitive_text = (
        "Kubernetes container deployment simplifies cluster scaling. "
        "Kubernetes container deployment accelerates production release cycles. "
        "Kubernetes container deployment ensures declarative state reconciliation. "
        "Kubernetes container deployment eliminates manual configuration."
    )
    ngrams = detect_repeated_ngrams(repetitive_text, n=3, threshold=3)
    assert len(ngrams) > 0
    assert any("kubernetes container deployment" in n.lower() for n in ngrams)
