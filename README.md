# 🎓 Shashwat AI:Course Recommender For Nepali Students

**Shashwat AI** is a data-driven career guidance tool designed for Nepali +2 students. It uses a hybrid approach—combining academic eligibility rules with a Machine Learning model—to recommend undergraduate courses based on GPA, stream, interests, and career goals.

## 📁 Project Structure

```text

│
├── app.py                  # FastAPI Backend (Main Entry Point)
├── requirements.txt        # Python dependencies
├── .gitignore              # Files to exclude from Git
│
├── /Model_Training         # Model development folder
│   ├── main.ipynb          # Notebook to train model & export JSON
│   └── /Data               # Raw CSV datasets
│
├── /static                 # Frontend assets
    ├── index.html          # Web UI
    ├── script.js           # Frontend logic
    └── style.css           # Styling
```

---

## 🛠️ Setup and Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/shashwatpokharel27/shashwatpokharel27-dotcom.git
   cd shashwatpokharel27-dotcom
   ```
2. **Environment Setup:**
   ```bash
   python -m venv myenv
     # On Windows
   myenv\Scripts\activate
   
   # On Mac/Linux
   source myenv/bin/activate
  ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧠 Workflow: Generating Required Files

Before running the FastAPI application, you must generate the trained model and the suggestion dataset.

1. Navigate to the `Model_Training` folder.
2. Open and run **`main.ipynb`**.
3. This notebook performs the following:
   * Processes the raw CSV files located in the `/Data` subfolder.
   * Trains the **Random Forest** recommendation model.
   * **Exports:**
     * `course_recommender_Rf.pkl` (The ML Model)
     * `label_encoder.pkl` (The Label Mapping)
     * `suggestions.json` (The dynamic autocomplete data)
4. Ensure these exported files are placed in the root directory (or as specified in `app.py`) after extraction.

---

## 🚀 Running the Application

Once the `.pkl` and `.json` files are extracted, start the web server:
```bash
uvicorn app:app --reload
```

Open your browser and navigate to `[http://127.0.0.1:8000](http://127.0.0.1:8000)` to use the recommender.

---
## 🌟 Key Features

*   **Hybrid Filtering:** Checks RJU/TU/KU/PU academic eligibility (GPA/Stream) before applying AI logic.
*   **Dynamic UI:** The `suggestions.json` file automatically populates the autocomplete fields in the frontend.
*   **Clean Architecture:** Separates model training logic (`main.ipynb`) from the production server (`app.py`).

---
*Bridging the gap between high school and higher education in Nepal.*

## 👤 Author

**Shashwat Pokharel**

- 📧 Email:shashwatpokharel27@gmail.com  
- 🔗 GitHub: https://github.com/shashwatpokharel27-dotcom  
- 💼 LinkedIn: https:/www.linkedin.com/in/shashwat-pokharel/ 
```
