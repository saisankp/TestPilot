import matplotlib.pyplot as plt
import numpy as np

types_of_testpilot = {
    'Default TestPilot': (90, 82, 92),
    'TestPilot without fine-tuning': (86, 74, 56),
}
metrics = ("Compilation", "Test accuracy", "Documentation")
width_of_bar = 0.25
offset_space = 0
x = np.arange(len(metrics))
fig, ax = plt.subplots(figsize=(10, 6))
for type_of_testpilot, rate in types_of_testpilot.items():
    offset = width_of_bar * offset_space
    offset_space += 1
    bar = ax.bar(x + offset, rate, width_of_bar, label=type_of_testpilot)
    ax.bar_label(bar, fmt='%d%%', padding=0, fontsize='10')
ax.set_title('Default TestPilot vs TestPilot without fine-tuning', fontsize=19, pad=10)
ax.set_xticks(x + 0.12)
ax.set_xticklabels(metrics, fontsize=16)
ax.set_ylabel('Rate (%)', fontsize=16, labelpad=-1)
ax.set_ylim(0, 100)
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.07), ncol=2, fontsize=16)
plt.tight_layout()
plt.savefig("plots/fine_tuning.png")
plt.show()
