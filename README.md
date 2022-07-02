Some students prefer to copy the work of other students. We created a simple find-clones program to automate the checking process.

To develop an algorithm, we first have to determine the type of copying we want to detect. We want to find a completely copied section with minor changes because it indicates that the student did nothing. Hence, the algorithm does not really understand the work it is analyzing. Student work is a Jupyter notebook, so it contains both text and code. We will consider them separately.

The steps in the duplicate search algorithm in texts are as follows:

1. Data cleaning entails deleting characters, changing case, and so on
2. Tokenization is a text-splitting technique (shingles)
3. Stop Words Removal: removing commonly used words
4. Stemming is the process of reducing words to their root forms (stems)
5. Statistical analysis to detect duplicates

Hence, we can use only language rules. So, we used the NLTK library, which has stop words and stemming for various languages.

Duplicate search algorithms for code may be more complex since some of them attempt to determine a syntactic structure as well. However, because we only need to solve a simple problem, we can use text methods such as the fingerprint method, which is very similar to the one described abov

A database of students' work is an essential component of the entire checking process. In order to make it more convenient, we tried Google Drive. It is convenient to load work, but downloading is not fast. So this approach is actually not suitable for large-audience courses. Nevertheless, the program works. And we tested that it helps to detect cheating.
