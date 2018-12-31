import re
import urllib.request
import os
import glob
import pathlib   
import time

class BlogImageAutoSyncer:
    base_dir = "/tmp/blog_image_auto_syncer"

    source_dir_path = "/source/_posts/"
    target_dir_path = "/images/"
    sleep_interval = 0.5

    # http|https://(*?.jpg|png|jpeg|gif|bmp)
    regex = "(http|https)://[^)]{1,200}/([^/)]{1,100}.jpg|png|jpeg|gif|bmp)"
    pattern = re.compile(regex)
    
    def __init__(self, source_git_url, target_git_url):
        self.source_git_url = source_git_url
        self.target_git_url = target_git_url
        self.source_git_local_dir = self.base_dir + '/source'
        self.target_git_local_dir = self.base_dir + '/target'
        self.source_pages_dir =  self.source_git_local_dir + '/' + self.source_dir_path
        self.target_images_dir =  self.target_git_local_dir + '/' + self.target_dir_path

    def run(self):
        self._prepare()
        full_image_list = BlogImageAutoSyncer._get_image_list(self.source_pages_dir)
        already_image_list = BlogImageAutoSyncer._get_file_name_list(self.target_images_dir)
        diff_image_list = full_image_list.copy()
        information = "auto sync image count:{} ; with_full_image_count:{}, target_exist_image_count:{}".format(len(diff_image_list), len(full_image_list), len(already_image_list))
        print(information)
        print('downloading started')
        for image_key in already_image_list:
            if image_key in diff_image_list:
                diff_image_list.pop(image_key, None)
        BlogImageAutoSyncer._download_images(diff_image_list, self.target_images_dir)
        print('downloading finished')
        self._post_action(len(diff_image_list), information)

    def _prepare(self):
        os.system("rm -rf " + self.base_dir)
        os.system("mkdir " + self.base_dir)
        os.system("git clone {git_address} {local_path}".format(git_address=self.source_git_url, local_path=self.source_git_local_dir))
        os.system("git clone {git_address} {local_path}".format(git_address=self.target_git_url, local_path=self.target_git_local_dir))

    def _post_action(self, sync_count, message):
        if sync_count > 0:
            print('start upload to target github repo')
            os.system("cd " + self.target_git_local_dir)
            os.system("git pull")
            os.system("git commit -m \"{}\"".format(message))
            os.system("git push")
            print('finished upload to target github repo')
        else:
            print('incremental as 0 no need to upload to github')   

    @staticmethod
    def _get_image_list(source_file_dir):
        file_list = BlogImageAutoSyncer._get_file_list(source_file_dir, 'md')
        image_list = {}
        for single_file in file_list:
            file_content = BlogImageAutoSyncer._get_content_from_file(single_file)
            single_image_list = BlogImageAutoSyncer._get_image_links_from_content(file_content)
            image_list.update(single_image_list)
        return image_list

    @staticmethod
    def _download_images(image_list, local_dir_path):
        for item in image_list.values():
            print('start download image: ' + item['url'])
            urllib.request.urlretrieve(item['url'], local_dir_path + item['key'])
            time.sleep(BlogImageAutoSyncer.sleep_interval)

    @staticmethod
    def _get_image_links_from_content(content):
        dic = {}
        for match in BlogImageAutoSyncer.pattern.finditer(content):
            key = match.group(2)
            url = match.group(0)
            dic[key] = {'key': key, 'url': url}
        return dic

    @staticmethod
    def _get_file_name_list(folder_dir):
        file_name_list = []
        file_list =  BlogImageAutoSyncer._get_file_list(folder_dir)
        print()
        for file_path in file_list:
            file_name_list.append(os.path.basename(file_path))
        return file_name_list  

    @staticmethod
    def _get_file_list(folder_dir, suffix='*'):
        file_list = []
        for file_path in pathlib.Path(folder_dir).glob('**/*.' + suffix):
            file_list.append(str(file_path))
        return file_list

    @staticmethod
    def _get_content_from_file(file_path):
        with open(file_path) as f:
            file_content = f.read()
        return file_content


source_git_url = "https://github.com/vanjor/VanjorBlogWebsite.git"
target_git_url = "git@github.com:vanjor/VanjorAssetWebsite.git"

syncer = BlogImageAutoSyncer(source_git_url, target_git_url)
syncer.run()

