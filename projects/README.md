# Projects

[Beyond Prediction Error](https://standardgalactic.github.io/laboratory/projects/beyond-prediction-error.pdf)

[The Sproll Curriculum](https://standardgalactic.github.io/laboratory/projects/sproll-monograph.pdf)


# Random Oracle

`random-oracle.sh` turns the repository into a small bibliomantic reading device. Each invocation searches the current directory recursively for Markdown, plain-text, and LaTeX files, selects one at random, chooses a random position within it, and prints a short passage.

Run it from the repository root:

```bash
chmod +x random-oracle.sh
./random-oracle.sh
```

You can also give it one or more directories to search:

```bash
./random-oracle.sh essays/
./random-oracle.sh projects/ notes/
```

The oracle ignores `.git` contents and temporary editor files. It never modifies the selected document. If it cannot find a supported file, it chooses a title from its small built-in fallback library.

Because selection occurs at both the file and line levels, repeated invocations expose fragments that ordinary navigation tends to miss:

```bash
./random-oracle.sh
./random-oracle.sh
./random-oracle.sh
```

The results may be treated as reading prompts, rediscovered ideas, accidental correspondences, or simply invitations to resume neglected work. The oracle does not claim that randomness produces meaning; it supplies a mechanism through which scattered parts of the repository can encounter one another.

![](eloi-poster.png)
![](aniara-poster.png)
![](city-of-brutes-poster.png)
![](konigsberg-poster.png)
![](incoherence-poster.png)
![](flower-wars-poster.png)
<!-- ![](flower-horizon-poster.png) -->
![](horizon-poster.png)
![](yarncrawlers-poster.png)
