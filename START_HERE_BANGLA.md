# Career Copilot Lab চালানোর সহজ নিয়ম

এটি Team NO AI-এর local AI Lab prototype। GPT/Gemini API key, MySQL বা paid hosting লাগবে না।

## Windows-এ প্রথমবার

1. পুরো ZIP download করো। ZIP-এর ভেতর থেকে সরাসরি file চালাবে না।
2. ZIP-এর ওপর right-click → **Extract All** করো।
3. Python **3.12** install করো। Installer-এ **Add Python to PATH** tick দাও। আগে থাকলে আবার install করার দরকার নেই।
4. Extract করা `career_copilot_lab` folder খোলো। এখানে `app.py` এবং `START_WINDOWS.bat` থাকবে।
5. **START_WINDOWS.bat** double-click করো। প্রথমবার internet লাগবে; প্রয়োজনীয় packages install হবে।
6. Black terminal window খোলা রাখো। প্রথম setup শেষ হতে কয়েক মিনিট লাগতে পারে।
7. Browser না খুললে address bar-এ `http://localhost:8501` লিখে Enter দাও।
8. **Create account** tab খোলো। Name, username, অন্তত ৮ অক্ষরের password এবং confirm password দাও। Storage consent tick করে account তৈরি করো।
9. **Sign in** tab-এ গিয়ে নতুন username/password দিয়ে ঢোকো।
10. বাম পাশের **Practice** থেকে task নির্বাচন করো। Code লিখে **Run tests & save attempt** চাপো।

Python-এ শুধু ছোট হাতের `solve` নামের function লিখবে। `input()` বা `print()` নয়, **return** ব্যবহার করবে।

## প্রথম demo: ভুল থেকে সঠিক

1. Practice → **L1 · Sum from 1 to n** নির্বাচন করো।
2. **Load a buggy example** চাপো, তারপর **Run tests & save attempt**।
3. Expected/Actual result দেখো। এই code শেষ সংখ্যাটি যোগ করে না।
4. **Show next hint** চাপো। এটি hint usage save করে।
5. Code-এর `range(1, n)` বদলে `range(1, n+1)` করো। আবার run করো।
6. সব test pass হবে। Hint দেখেছ বলে attempt-টি assisted থাকবে; এটি সঠিক behaviour।
7. **Overview** এবং **History** খোলো। Saved result দেখতে পাবে।
8. **My skills & CV**-তে `Python, SQL, React` paste করো, **Extract skill keywords**, তারপর **Save skill profile** চাপো।
9. Python task evidence দেখাবে। SQL/React এই version-এ **Not assessed** থাকবে।
10. **Learning roadmap** এবং **Model lab** খুলে adaptive plan ও actual training metrics দেখাও।

## পরে আবার চালাতে

একই folder-এর `START_WINDOWS.bat` double-click করলেই হবে। Dependencies থাকলে internet লাগে না। আগের account, profile ও history `data/career.db`-তে থাকে। Folder সরালে পুরো folder একসঙ্গে সরাবে। Terminal বন্ধ করলে app বন্ধ হবে, data মুছবে না।

## যদি double-click কাজ না করে

Project folder-এর address bar-এ `cmd` লিখে Enter দাও। একেকটি command একেকবার চালাও:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe bootstrap.py
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

`py` পাওয়া না গেলে প্রথম command-এ `py -3.12`-এর বদলে `python` ব্যবহার করো।

## সাধারণ সমস্যা

- **Python not found:** Python 3.12 install করে PATH option tick করো; নতুন terminal খোলো।
- **Python version unsupported:** 3.12 ব্যবহার করো। এই project-এর supported versions 3.11-3.13।
- **Package install failed:** internet connection এবং error message check করো। Screenshot দাও; security setting বন্ধ করবে না।
- **Port already in use:** আগের app-এর terminal বন্ধ করো, অথবা launch command-এর port `8502` করে `http://localhost:8502` খোলো।
- **Model version changed:** `RETRAIN_WINDOWS.bat` চালাও; app refresh করো।
- **Unsupported Python feature:** Runner help পড়ো। `.append()`-এর বদলে `result = result + [n]` ব্যবহার করো।
- **Step limit reached:** infinite loop অথবা অতিরিক্ত কাজ আছে। Loop-এর variable update হচ্ছে কি না দেখো।
- **CV scan থেকে skill আসে না:** scanned PDF-এ OCR নেই; text paste করো অথবা manually skill select করো।
- **Password ভুলে গেলে:** email recovery এই local prototype-এ নেই। নতুন username দিয়ে account খোলা যায়; পুরোনো account-এ প্রবেশ করা যাবে না।

## Testing ও training

- **RUN_TESTS_WINDOWS.bat:** automated test suite চালাবে।
- **RETRAIN_WINDOWS.bat:** included generated pilot dataset দিয়ে model আবার train করবে।
- **Model lab:** Logistic Regression/SVM comparison, Accuracy, Macro-F1, Recall এবং confusion matrix দেখাবে।

## Submission-এর আগে যা বুঝতে হবে

এই build-এ **নিজেদের training code ও trained classifier আছে**, কিন্তু training data generated এবং pilot-level। এটি real student data নয়। Human review ও independent real data ছাড়া “real-world accuracy” দাবি করবে না।

Code runner শুধুমাত্র basic Python subset support করে। এটি local lab demonstration-এর জন্য। Public link বা internet-facing server হিসেবে deploy করবে না; সেজন্য আলাদা security work প্রয়োজন।

এই code নিজেরা run করে বুঝবে এবং course-এর AI-use policy মেনে assistance disclose করবে। Team-এর তিনজনের নাম এখনো পাওয়া যায়নি; submission-এর আগে README ও app-এর team list-এ নাম যোগ করবে।
