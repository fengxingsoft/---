import os
import time
import pickle
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import jieba

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DouyinUploaderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("抖音视频上传工具")
        self.root.geometry("820x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#f6f8fa")

        self.cookies_file = "douyin_cookies.pkl"
        self.driver = None
        self.video_path = ""

        self.create_widgets()
        self.setup_driver_and_cookies()

    def create_widgets(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure("TButton", font=("微软雅黑", 11), padding=5)
        s.configure("TLabel", font=("微软雅黑", 11), background="#f6f8fa")
        s.configure("TEntry", font=("微软雅黑", 11), padding=3)
        s.configure("TFrame", background="#f6f8fa")
        s.configure("TLabelframe", background="#f6f8fa", font=("微软雅黑", 12, "bold"))
        s.configure("TLabelframe.Label", font=("微软雅黑", 12, "bold"), background="#f6f8fa")

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # 视频信息分组
        video_group = ttk.LabelFrame(main_frame, text="视频信息")
        video_group.grid(row=0, column=0, sticky="ew", padx=0, pady=0, ipadx=3, ipady=6)
        video_group.columnconfigure(1, weight=1)

        ttk.Label(video_group, text="视频路径:").grid(row=0, column=0, sticky="w", pady=5)
        self.video_entry = ttk.Entry(video_group, width=70)
        self.video_entry.grid(row=0, column=1, sticky="ew", padx=(0,8))
        ttk.Button(video_group, text="选择视频", command=self.select_video).grid(row=0, column=2, sticky="w", padx=(0,10))

        ttk.Label(video_group, text="标题:").grid(row=1, column=0, sticky="w", pady=5)
        self.title_entry = ttk.Entry(video_group, width=70)
        self.title_entry.grid(row=1, column=1, sticky="ew", padx=(0,8), columnspan=2)

        # 描述分组
        desc_group = ttk.LabelFrame(main_frame, text="视频描述与标签")
        desc_group.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        desc_group.columnconfigure(0, weight=1)

        self.desc_text = tk.Text(desc_group, height=7, width=75, font=("微软雅黑", 11))
        self.desc_text.grid(row=0, column=0, sticky="ew", padx=2, pady=5, columnspan=3)

        ttk.Button(desc_group, text="试一下（自动生成标签）", command=self.try_recommend_tags).grid(row=1, column=0, sticky="w", pady=5, padx=1)
        ttk.Label(desc_group, text="提示：将标签自动添加到描述末尾").grid(row=1, column=1, sticky="w", padx=8)

        # 操作分组
        ops_group = ttk.LabelFrame(main_frame, text="操作")
        ops_group.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        ops_group.columnconfigure((0,1,2), weight=1)

        ttk.Button(ops_group, text="检测登录状态", width=20, command=self.check_login_status).grid(row=0, column=0, padx=16, pady=12)
        ttk.Button(ops_group, text="上传视频", width=20, command=self.upload_video).grid(row=0, column=1, padx=16, pady=12)

    def select_video(self):
        path = filedialog.askopenfilename(filetypes=[["视频文件", "*.mp4 *.mov *.avi *.mkv"]])
        if path:
            self.video_path = path
            self.video_entry.delete(0, tk.END)
            self.video_entry.insert(0, path)

    def setup_driver_and_cookies(self):
        try:
            self.driver = webdriver.Chrome()
            self.driver.maximize_window()
            self.driver.get("https://creator.douyin.com/creator-micro/content/upload")
            if self.load_cookies():
                self.driver.refresh()
                if self.is_logged_in():
                    logging.info("Cookie登录成功")
                    return
            self.login()  # 只有cookie无效才扫码
        except Exception as e:
            logging.error(f"浏览器启动或登录流程失败: {e}")
            messagebox.showerror("错误", f"浏览器启动或登录流程失败: {e}")

    def save_cookies(self):
        try:
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(self.driver.get_cookies(), f)
            logging.info("Cookies 已保存")
        except Exception as e:
            logging.warning(f"保存 Cookies 失败: {e}")

    def load_cookies(self):
        if not os.path.exists(self.cookies_file):
            return False
        try:
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    if 'sameSite' in cookie:
                        del cookie['sameSite']
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception:
                        continue
            logging.info("Cookies 已加载")
            return True
        except Exception as e:
            logging.warning(f"加载 Cookies 失败: {e}")
            return False

    def is_logged_in(self):
        try:
            self.driver.get("https://creator.douyin.com/creator-micro/content/upload")
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            return True
        except Exception:
            return False

    def check_login_status(self):
        if self.driver is None:
            self.setup_driver_and_cookies()
        status = self.is_logged_in()
        if status:
            messagebox.showinfo("登录状态", "账号已登录")
        else:
            messagebox.showwarning("登录状态", "账号未登录")

    def login(self):
        self.driver.get("https://www.douyin.com/login")
        messagebox.showinfo("登录提示", "请在浏览器中手动登录抖音账号，登录完成后点击 OK")
        while True:
            if self.is_logged_in():
                self.save_cookies()
                break
            answer = messagebox.askyesno("登录检测", "未检测到已登录，是否已完成扫码登录？（是=重试检测，否=继续扫码）")
            if not answer:
                break

    def ensure_driver_alive(self):
        try:
            _ = self.driver.title
        except WebDriverException:
            logging.warning("检测到 driver 无效，尝试重启浏览器...")
            self.setup_driver_and_cookies()

    def wait_for_upload_complete(self):
        try:
            publish_btn = WebDriverWait(self.driver, 300).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '发布')]"))
            )
            return publish_btn
        except Exception as e:
            logging.error(f"等待上传完成超时: {e}")
            return None

    def wait_for_machine_check(self):
        try:
            WebDriverWait(self.driver, 180).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//*[contains(text(),'作品未见异常') or contains(text(),'温馨提示') or contains(text(),'结果由机器检测提供') or contains(text(),'重新检测')]")
                )
            )
            logging.info("机器检测已通过或检测提示出现，可以发布。")
            return True
        except Exception as e:
            logging.warning(f"机器检测提示未出现: {e}")
            return False

    def try_recommend_tags(self):
        title = self.title_entry.get()
        desc = self.desc_text.get("1.0", tk.END)
        text = title + ' ' + desc

        words = jieba.lcut(text)
        stop_words = set(['的', '了', '在', '是', '我', '和', '就', '都', '也', '很', '与', '为', '你', '他', '她', '它', '不', '这', '有', '到', '上', '下', '吧', '吗'])
        counter = {}
        for w in words:
            if len(w) > 1 and w not in stop_words:
                counter[w] = counter.get(w, 0) + 1
        sorted_words = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        tags = [w for w, _ in sorted_words[:5]]
        tags_string = ' '.join(f'#{tag}#' for tag in tags)

        desc_current = self.desc_text.get("1.0", tk.END).strip()
        if desc_current and not desc_current.endswith('\n'):
            desc_current += '\n'
        desc_with_tags = desc_current + tags_string
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert(tk.END, desc_with_tags)

        messagebox.showinfo("推荐标签", f"已为你自动补全标签到描述末尾：{tags_string}")

    def upload_video(self):
        self.ensure_driver_alive()

        if not self.video_path:
            messagebox.showwarning("警告", "请先选择视频文件")
            return

        if not self.is_logged_in():
            if self.load_cookies():
                self.driver.refresh()
                if self.is_logged_in():
                    logging.info("Cookie登录成功，进入上传流程")
                else:
                    self.login()
            else:
                self.login()

        self.driver.get("https://creator.douyin.com/creator-micro/content/upload")
        try:
            file_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(os.path.abspath(self.video_path))
            logging.info("已选择视频")

            publish_button = self.wait_for_upload_complete()
            if not publish_button:
                raise Exception("上传超时，视频未成功上传")
            logging.info("视频上传完成，准备填写表单")

            title = self.title_entry.get().strip()
            for _ in range(3):
                try:
                    title_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.semi-input"))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
                    title_input.clear()
                    title_input.send_keys(title)
                    break
                except Exception as e:
                    logging.warning(f"设置标题失败，重试中: {e}")
                    time.sleep(1)

            desc = self.desc_text.get("1.0", tk.END).strip().replace("`", "'")
            for _ in range(3):
                try:
                    WebDriverWait(self.driver, 10).until_not(
                        EC.presence_of_element_located((By.CLASS_NAME, "semi-toast-content"))
                    )
                    editor = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][data-slate-editor='true']"))
                    )
                    self.driver.execute_script("arguments[0].focus();", editor)
                    set_desc_script = f"arguments[0].innerText = `{desc}`;"
                    self.driver.execute_script(set_desc_script, editor)
                    break
                except Exception as e:
                    logging.warning(f"设置描述失败，重试中: {e}")
                    time.sleep(1)

            if not self.wait_for_machine_check():
                messagebox.showwarning("警告", "机器检测未通过或超时，建议人工检查")
                return

            time.sleep(2)

            publish_button.click()
            logging.info("已点击发布")
            messagebox.showinfo("成功", "视频上传并发布成功！")

        except Exception as e:
            if "invalid session id" in str(e).lower():
                logging.warning("会话失效，重启浏览器重试...")
                self.setup_driver_and_cookies()
                self.upload_video()
                return
            logging.error(f"上传失败: {e}")
            messagebox.showerror("错误", f"上传失败: {e}")

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = DouyinUploaderGUI()
    app.run()